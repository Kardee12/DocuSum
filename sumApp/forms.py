from django import forms
from django.core.validators import FileExtensionValidator


class SummarizationForm(forms.Form):
    uploadFile = forms.FileField(
        required = False,
        widget = forms.FileInput(attrs = {'class': 'form-control', 'accept': '.txt,.csv,.docx,.doc,.pdf'}),
        validators = [FileExtensionValidator(allowed_extensions = ['pdf', 'doc', 'docx', 'txt', 'csv'])]
    )
    textInput = forms.CharField(
        required = False,
        widget = forms.Textarea(attrs = {'class': 'form-control', 'rows': 5, 'placeholder': 'Paste your text here'})
    )
    model = forms.ChoiceField(
        choices = [('BART', 'BART'), ('FLAN-T5', 'FLAN-T5')],
        widget = forms.Select(attrs = {'class': 'form-select', 'onchange': 'handleModelChange()', 'id': 'id_model'})
    )
    minTokens = forms.IntegerField(
        required = False,
        widget = forms.NumberInput(
            attrs = {'class': 'form-control', 'placeholder': 'Min Tokens', 'id': 'id_minTokens'}),
        min_value = 1
    )
    maxTokens = forms.IntegerField(
        required = False,
        widget = forms.NumberInput(
            attrs = {'class': 'form-control', 'placeholder': 'Max Tokens', 'id': 'id_maxTokens'}),
        min_value = 1
    )

    def clean(self):
        cleaned_data = super().clean()
        uploadFile = cleaned_data.get('uploadFile')
        textInput = cleaned_data.get('textInput')
        model_choice = cleaned_data.get('model')

        if not uploadFile and not textInput:
            raise forms.ValidationError("Please fill either the 'Upload File' or 'Text Input' field.")

        if uploadFile and textInput:
            raise forms.ValidationError("Fill only one of the 'Upload File' or 'Text Input' fields, not both.")

        # For models other than FLAN-T5, check token values
        if model_choice != 'FLAN-T5':
            minTokens = cleaned_data.get('minTokens')
            maxTokens = cleaned_data.get('maxTokens')

            if not minTokens or not maxTokens:
                raise forms.ValidationError("Minimum and maximum tokens are required for this model.")

            if maxTokens < (minTokens + 3):
                raise forms.ValidationError("Maximum tokens must be at least 3 greater than minimum tokens.")

        return cleaned_data


class TranslationForm(forms.Form):
    uploadFile = forms.FileField(
        required = False,
        widget = forms.FileInput(
            attrs = {'class': 'form-control', 'accept': '.txt,.csv,.docx,.doc,.pdf'}
        ),
        validators = [
            FileExtensionValidator(
                allowed_extensions = ['pdf', 'doc', 'docx', 'txt', 'csv'])],
    )
    textInput = forms.CharField(
        required = False,
        widget = forms.Textarea(
            attrs = {'class': 'form-control', 'rows': 5, 'placeholder': 'Paste your text here'}
        )
    )
    model = forms.ChoiceField(
        choices = [('MBART', 'MBART')],
        widget = forms.Select(
            attrs = {'class': 'form-select'}
        )
    )

    langTTF = forms.ChoiceField(
        choices = [
            ("ar_AR", "Arabic"),
            ("cs_CZ", "Czech"),
            ("de_DE", "German"),
            ("en_XX", "English"),
            ("es_XX", "Spanish"),
            ("et_EE", "Estonian"),
            ("fi_FI", "Finnish"),
            ("fr_XX", "French"),
            ("gu_IN", "Gujarati"),
            ("hi_IN", "Hindi"),
            ("it_IT", "Italian"),
            ("ja_XX", "Japanese"),
            ("kk_KZ", "Kazakh"),
            ("ko_KR", "Korean"),
            ("lt_LT", "Lithuanian"),
            ("lv_LV", "Latvian"),
            ("my_MM", "Burmese"),
            ("ne_NP", "Nepali"),
            ("nl_XX", "Dutch"),
            ("ro_RO", "Romanian"),
            ("ru_RU", "Russian"),
            ("si_LK", "Sinhala"),
            ("tr_TR", "Turkish"),
            ("vi_VN", "Vietnamese"),
            ("zh_CN", "Chinese"),
            ("af_ZA", "Afrikaans"),
            ("az_AZ", "Azerbaijani"),
            ("bn_IN", "Bengali"),
            ("fa_IR", "Persian"),
            ("he_IL", "Hebrew"),
            ("hr_HR", "Croatian"),
            ("id_ID", "Indonesian"),
            ("ka_GE", "Georgian"),
            ("km_KH", "Khmer"),
            ("mk_MK", "Macedonian"),
            ("ml_IN", "Malayalam"),
            ("mn_MN", "Mongolian"),
            ("mr_IN", "Marathi"),
            ("pl_PL", "Polish"),
            ("ps_AF", "Pashto"),
            ("pt_XX", "Portuguese"),
            ("sv_SE", "Swedish"),
            ("sw_KE", "Swahili"),
            ("ta_IN", "Tamil"),
            ("te_IN", "Telugu"),
            ("th_TH", "Thai"),
            ("tl_XX", "Tagalog"),
            ("uk_UA", "Ukrainian"),
            ("ur_PK", "Urdu"),
            ("xh_ZA", "Xhosa"),
            ("gl_ES", "Galician"),
            ("sl_SI", "Slovene")
        ],
        widget = forms.Select(
            attrs = {'class': 'form-select'}
        )
    )

    langTTT = forms.ChoiceField(
        choices = [
            ("ar_AR", "Arabic"),
            ("cs_CZ", "Czech"),
            ("de_DE", "German"),
            ("en_XX", "English"),
            ("es_XX", "Spanish"),
            ("et_EE", "Estonian"),
            ("fi_FI", "Finnish"),
            ("fr_XX", "French"),
            ("gu_IN", "Gujarati"),
            ("hi_IN", "Hindi"),
            ("it_IT", "Italian"),
            ("ja_XX", "Japanese"),
            ("kk_KZ", "Kazakh"),
            ("ko_KR", "Korean"),
            ("lt_LT", "Lithuanian"),
            ("lv_LV", "Latvian"),
            ("my_MM", "Burmese"),
            ("ne_NP", "Nepali"),
            ("nl_XX", "Dutch"),
            ("ro_RO", "Romanian"),
            ("ru_RU", "Russian"),
            ("si_LK", "Sinhala"),
            ("tr_TR", "Turkish"),
            ("vi_VN", "Vietnamese"),
            ("zh_CN", "Chinese"),
            ("af_ZA", "Afrikaans"),
            ("az_AZ", "Azerbaijani"),
            ("bn_IN", "Bengali"),
            ("fa_IR", "Persian"),
            ("he_IL", "Hebrew"),
            ("hr_HR", "Croatian"),
            ("id_ID", "Indonesian"),
            ("ka_GE", "Georgian"),
            ("km_KH", "Khmer"),
            ("mk_MK", "Macedonian"),
            ("ml_IN", "Malayalam"),
            ("mn_MN", "Mongolian"),
            ("mr_IN", "Marathi"),
            ("pl_PL", "Polish"),
            ("ps_AF", "Pashto"),
            ("pt_XX", "Portuguese"),
            ("sv_SE", "Swedish"),
            ("sw_KE", "Swahili"),
            ("ta_IN", "Tamil"),
            ("te_IN", "Telugu"),
            ("th_TH", "Thai"),
            ("tl_XX", "Tagalog"),
            ("uk_UA", "Ukrainian"),
            ("ur_PK", "Urdu"),
            ("xh_ZA", "Xhosa"),
            ("gl_ES", "Galician"),
            ("sl_SI", "Slovene")
        ]
        ,
        widget = forms.Select(
            attrs = {'class': 'form-select'}
        )
    )

    def clean(self):
        cleaned_data = super().clean()
        uploadFile = cleaned_data.get('uploadFile')
        textInput = cleaned_data.get('textInput')

        if not uploadFile and not textInput:
            raise forms.ValidationError("Please fill either the 'Upload File' or 'Text Input' field.")

        if uploadFile and textInput:
            raise forms.ValidationError("Fill only one of the 'Upload File' or 'Text Input' fields, not both.")

        langTTF = cleaned_data.get('langTTF')
        langTTT = cleaned_data.get('langTTT')
        if langTTT == langTTF:
            raise forms.ValidationError("Please change one of the languages as they cannot be the same.")

        return cleaned_data


class QuestionForm(forms.Form):
    uploadFile = forms.FileField(
        required = False,
        widget = forms.FileInput(attrs = {'class': 'form-control', 'accept': '.txt,.csv,.docx,.doc,.pdf'}),
        validators = [FileExtensionValidator(allowed_extensions = ['pdf', 'doc', 'docx', 'txt', 'csv'])]
    )
    textInput = forms.CharField(
        required = False,
        widget = forms.Textarea(attrs = {'class': 'form-control', 'rows': 5, 'placeholder': 'Paste your text here'})
    )
    model = forms.ChoiceField(
        choices = [('ELECTRA', 'ELECTRA'), ('DISTILBERT', 'DISTILBERT'), ('ROBERTA', 'ROBERTA')],
        widget = forms.Select(attrs = {'class': 'form-select', 'onchange': 'handleModelChange()', 'id': 'id_model'})
    )
    question = forms.CharField(
        required = True,
        widget = forms.Textarea(attrs = {'class': 'form-control', 'rows': 1, 'placeholder': 'Specify your question'})
    )

    def clean(self):
        cleaned_data = super().clean()
        uploadFile = cleaned_data.get('uploadFile')
        textInput = cleaned_data.get('textInput')
        question = cleaned_data.get('question')

        if not uploadFile and not textInput:
            raise forms.ValidationError("Please fill either the 'Upload File' or 'Text Input' field.")

        if uploadFile and textInput:
            raise forms.ValidationError("Fill only one of the 'Upload File' or 'Text Input' fields, not both.")

        return cleaned_data


class SentimentAnalysisForm(forms.Form):
    uploadFile = forms.FileField(
        required = False,
        widget = forms.FileInput(attrs = {'class': 'form-control', 'accept': '.txt,.csv,.docx,.doc,.pdf'}),
        validators = [FileExtensionValidator(allowed_extensions = ['pdf', 'doc', 'docx', 'txt', 'csv'])]
    )
    textInput = forms.CharField(
        required = False,
        widget = forms.Textarea(attrs = {'class': 'form-control', 'rows': 5, 'placeholder': 'Paste your text here'})
    )
    model = forms.ChoiceField(
        choices = [('FLAN-T5', 'FLAN-T5')],
        widget = forms.Select(attrs = {'class': 'form-select', 'onchange': 'handleModelChange()', 'id': 'id_model'})
    )

    def clean(self):
        cleaned_data = super().clean()
        uploadFile = cleaned_data.get('uploadFile')
        textInput = cleaned_data.get('textInput')

        if not uploadFile and not textInput:
            raise forms.ValidationError("Please fill either the 'Upload File' or 'Text Input' field.")

        if uploadFile and textInput:
            raise forms.ValidationError("Fill only one of the 'Upload File' or 'Text Input' fields, not both.")

        return cleaned_data
