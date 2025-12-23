(function () {
  function dedupe(items) {
    var seen = new Set();
    var result = [];
    items.forEach(function (item) {
      var key = item.toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        result.push(item);
      }
    });
    return result;
  }

  function splitInput(value) {
    if (!value) {
      return [];
    }
    return value
      .split(/[,\n]+/)
      .map(function (part) {
        return part.trim();
      })
      .filter(function (part) {
        return part.length > 0;
      });
  }

  function buildChip(label) {
    var chip = document.createElement('span');
    chip.className = 'tag-chip';
    chip.dataset.value = label;

    var text = document.createElement('span');
    text.className = 'tag-label';
    text.textContent = label;
    chip.appendChild(text);

    var remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'tag-remove';
    remove.setAttribute('aria-label', 'Remove ' + label);
    remove.innerHTML = '×';
    chip.appendChild(remove);

    return chip;
  }

  function initWidget(root) {
    var chipList = root.querySelector('.taglist-chiplist');
    var input = root.querySelector('.taglist-input');
    var hidden = root.querySelector('input[type="hidden"]');
    if (!chipList || !input || !hidden) {
      return;
    }

    var values = dedupe(splitInput(hidden.value));

    function render() {
      while (chipList.firstChild) {
        chipList.removeChild(chipList.firstChild);
      }
      values.forEach(function (value) {
        chipList.appendChild(buildChip(value));
      });
      hidden.value = values.join('\n');
    }

    function addValue(raw) {
      var cleaned = (raw || '').trim();
      if (!cleaned) {
        return;
      }
      var lower = cleaned.toLowerCase();
      var exists = values.some(function (value) {
        return value.toLowerCase() === lower;
      });
      if (!exists) {
        values.push(cleaned);
        render();
      }
    }

    function removeValue(targetValue) {
      values = values.filter(function (value) {
        return value.toLowerCase() !== targetValue.toLowerCase();
      });
      render();
    }

    render();

    input.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ',') {
        event.preventDefault();
        addValue(input.value);
        input.value = '';
      } else if (event.key === 'Backspace' && input.value === '' && values.length) {
        event.preventDefault();
        values.pop();
        render();
      }
    });

    input.addEventListener('blur', function () {
      addValue(input.value);
      input.value = '';
    });

    chipList.addEventListener('click', function (event) {
      if (event.target.classList.contains('tag-remove')) {
        var chip = event.target.closest('.tag-chip');
        if (chip && chip.dataset.value) {
          removeValue(chip.dataset.value);
        }
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var widgets = document.querySelectorAll('.taglist-widget');
    widgets.forEach(initWidget);
  });
})();
