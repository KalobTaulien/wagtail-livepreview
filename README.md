# Wagtail Live Preview
> Wagtail Live Preview lets you view your page changes as you make them in the Wagtail Admin.

![](docs/LivePreview.gif)

**Using React or Vue?** This won't work for you, nor was it designed to. This Live Preview package is designed for simple Wagtail websites.

#### How it works
Tell it how often to save a snapshot of the page you're working on and how often to poll for updates in the Live Preview.

It does _not_ piggy back on Wagtails Revision system, but you can tell it to save a page revision every _x_ number of saves so you never accidentally lose your work (or if you just want to log your progress and maybe revert back to a previous content iteration).

The package itself is called `wagtail-livepreview` to let everyone know this is a Wagtail specific package. But the code references `livepreview` instead of `wagtail_livepreview` as to not confuse Wagtail features with what's in this package.

## Installation
1. Install the package
```bash
pip install wagtail-livepreview
```
2. Add it to your `INSTALLED_APPS` _above_ the `'wagtail.admin'` app.
```python
INSTALLED_APPS = [
    # ...
    'livepreview',
    # ...
    'wagtail.admin',
]
```
3. Add `{% load livepreview_tags %}` to your `base.html` template. And add `{% livepreview_js %}` right above your `</body>` tag in `base.html`

```html+Django
{% load static wagtailuserbar livepreview_tags %}

<!DOCTYPE html>
<html class="no-js" lang="en">
    <head>
        ...
    </head>

    <body class="{% block body_class %}{% endblock %}">
        ...

        {% livepreview_js %}
    </body>
</html>
```
4. You'll need to apply migrations.
```shell
python manage.py migrate
```

## Hooks
You can take an action before and after a Live Preview using a generic Wagtail hook.

```python
@hooks.register('after_live_preview_save')
def after_live_preview_save(request, page):
    """Event to happen before the live preview is served."""
    print(page.id)


@hooks.register('before_live_preview_save')
def before_live_preview_save(request, page):
    """Event to happen after the live preview is served."""
    print(page.id)
```

> **Caution:** It's a bad idea to provide a process intensive task in these hooks since these hooks may end up being called as frequently as once per second. It might be best to offload your tasks in these hooks to a task runner.

## Tips
### Checking if a view is a Live Preview or not
You'll want to adjust your template so you aren't triggering your analytics every second. You can prevent this with:

```html+Django
{% if not livepreview %}
    .. analytics in here
{% else %}
    <div id="warning">This is a live preview</div>
{% endif %}
```

You can also use `{{ request.livepreview }}` in your template to check against the `request`.

## Settings
#### Global Settings
```python
# base settings.py

# How often (in milliseconds) should the livepreview check for page updates? Default is 1000ms.
LIVEPREVIEW_TIMEOUT = 1000
# If you'd like to turn on auto-revision saving every x number of Live Preview saves, set this as True. Default is False.
LIVEPREVIEW_SAVE_AS_REVISIONS = False
# How many Live Preview saves should happen before a new revision is automatically saved? Default is 10. Requires LIVEPREVIEW_SAVE_AS_REVISIONS = True.
LIVEPREVIEW_SAVE_REVISION_COUNT = 10
# Render Live Previews into a temporary file, and attempt to serve that file. Default is true.
# If True, LIVEPREVIEW_TIMEOUT can be as low as 250ms.
# If False, the minimum LIVEPREVIEW_TIMEOUT is 1000ms.
LIVEPREVIEW_USE_FILE_RENDERING = True
```

#### Model Settings
You can disable Live Preview for specific page models. For example, you might have a simple Blog Index Page with just a `title` field. Or a page that redirects to another page. In these scenarios you might not want Live Preview enabled.
```python
class YourPage(Page):
    # ...
    LIVEPREVIEW_DISABLED = True  # Disable Live Preview on a per-model basis
```

## Contributing
Feel free to open a PR. I'm not overly picky about how things are done as long as it works and it's kept relatively simple.

The JavaScript can use _a lot_ of improvements (small and large) so that'd be a great place to start.

## @todos
If anyone wants to get involved and pick off a few of these tasks, that'd be awesome. But no pressure.
 - [ ] Implement proper http protocol responses
 - [ ] Remove jQuery in favor of vanilla JS
 - [ ] Put the iframe in the content_panels ONLY tab.
 - [ ] Make the iframe be 100% height of the content section
 - [ ] Add better JavaScript error handling and events
 - [ ] When `LIVEPREVIEW_USE_FILE_RENDERING` is enabled, save the LivePreview file with minified html (Not using middleware, and respects spacing in elements like `<pre>` and `<textarea>`)