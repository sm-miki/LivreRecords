from string import Template
from django.utils.safestring import mark_safe
from django import forms

class ImageWidget(forms.widgets.Widget):
	def render(self, name, value, attrs=None, **kwargs):
		html = Template("""<img src="$link"/>""")
		return mark_safe(html.substitute(link=value or ''))
