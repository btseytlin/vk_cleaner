from django import forms
from urllib.parse import urlparse, parse_qs
class AuthInfoForm(forms.Form):
    vk_link = forms.CharField(label='ссылка авторизации', max_length=400)

    def clean_vk_link(self):
        vk_link = self.cleaned_data['vk_link']
        parse_result = urlparse(vk_link)
        if not parse_result.scheme and not parse_result.netloc:
            raise forms.ValidationError("Неверный формат ссылки", code='not_url')
        elif not 'vk.com' in parse_result.netloc:
            raise forms.ValidationError("Ссылка должна содержать \"vk.com\"", code='not_vk_url')
        try:
            params = parse_qs(urlparse(vk_link).fragment)
            access_token = params['access_token'][0]
            user_id = params['user_id'][0]
        except:
            raise forms.ValidationError("Ссылка должна содержать access_token и user_id", code='no_access_token_user_id')

        return vk_link
