from django.test import SimpleTestCase, RequestFactory
from django.http import HttpResponseRedirect, HttpResponse
import json

from fishy_friend_aquatics.middleware import AjaxLoginRedirectMiddleware


class AjaxLoginRedirectMiddlewareTests(SimpleTestCase):
	def setUp(self):
		self.factory = RequestFactory()
		self.middleware = AjaxLoginRedirectMiddleware(lambda req: HttpResponse())

	def test_ajax_redirect_converted_to_json_401(self):
		# Simulate an AJAX request that receives a redirect to login
		req = self.factory.get('/checkout/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		resp = HttpResponseRedirect('/login/?next=/checkout/')
		out = self.middleware.process_response(req, resp)
		self.assertEqual(out.status_code, 401)
		data = json.loads(out.content.decode('utf-8'))
		self.assertIn('message', data)
		self.assertTrue('auth' in data['message'].lower() or 'authentication' in data['message'].lower())

	def test_non_ajax_redirect_unchanged(self):
		req = self.factory.get('/checkout/')
		resp = HttpResponseRedirect('/login/?next=/checkout/')
		out = self.middleware.process_response(req, resp)
		# non-AJAX should return the original redirect
		self.assertEqual(out.status_code, 302)


from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from store.models import Category, Breed, Fish, Cart, Coupon


class ApplyCouponIntegrationTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.username = 'itestuser'
		self.password = 'pass12345'
		User.objects.filter(username=self.username).delete()
		self.user = User.objects.create_user(username=self.username, password=self.password, role='customer', email='i@test.local')
		# Create product and add to cart
		cat, _ = Category.objects.get_or_create(name='IntCat')
		breed, _ = Breed.objects.get_or_create(name='IntBreed', category=cat)
		fish, _ = Fish.objects.get_or_create(name='IntFish', defaults={
			'category': cat,
			'breed': breed,
			'description': 'Integration fish',
			'price': Decimal('100.00'),
			'stock_quantity': 10,
			'minimum_order_quantity': 1,
			'is_available': True,
		})
		Cart.objects.filter(user=self.user).delete()
		Cart.objects.create(user=self.user, fish=fish, quantity=1)

	def test_ajax_post_apply_coupon_unauthenticated_saves_in_session(self):
		url = '/apply-coupon/'
		resp = self.client.post(url, {'coupon_code': 'NOPE'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		# Anonymous users should be able to save a coupon code in session
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(data.get('success'))
		session = self.client.session
		self.assertEqual(session.get('applied_coupon_code'), 'NOPE')

	def test_authenticated_apply_coupon_success(self):
		# create coupon
		now = timezone.now()
		Coupon.objects.filter(code='ITEST10').delete()
		Coupon.objects.create(code='ITEST10', discount_percentage=Decimal('10.0'), max_discount_amount=Decimal('1000.00'), min_order_amount=Decimal('0.00'), coupon_type='all', is_active=True, show_in_suggestions=True, valid_from=now - timedelta(days=1), valid_until=now + timedelta(days=7), usage_limit=100, times_used=0, created_by=None)

		logged = self.client.login(username=self.username, password=self.password)
		self.assertTrue(logged)
		resp = self.client.post('/apply-coupon/', {'coupon_code': 'ITEST10'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(data.get('success'))
		# Session should have applied coupon
		session = self.client.session
		self.assertEqual(session.get('applied_coupon_code'), 'ITEST10')

