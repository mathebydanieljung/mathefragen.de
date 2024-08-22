from django.db import models


class Global(models.Model):
    # in future, our own editors
    EDITORS = (
        ('tiny', 'TinyMCE'),
        ('md', 'Markdown')
    )
    logo = models.FileField(
        upload_to='project/logo/',
        default='',
        blank=True,
        help_text='Ja: PNG, JPG, JPEG... Nein: PDF, MP4 und alles was kein Logo sein kann.'  # noqa
    )
    logo_svg_content = models.TextField(
        default='',
        blank=True
    )
    logo_icon = models.FileField(
        upload_to='project/logo/icon/',
        blank=True,
        default='',
        help_text='Ja: PNG, JPG, JPEG... Nein: PDF, MP4 und alles was kein Logo sein kann.'  # noqa
    )
    logo_icon_svg_content = models.TextField(
        default='',
        blank=True
    )
    ci_color = models.CharField(
        max_length=50,
        default='#03689e',
        help_text='CI Farbe als Hex Code'  # noqa
    )
    question_editor = models.CharField(
        max_length=20,
        choices=EDITORS,
        default='tiny'
    )

    slogan = models.TextField(
        default='',
        help_text='Dieser Text erscheint in Registrierung- & Loginseiten.',
        blank=True
    )

    def __str__(self):
        return 'Globale Einstellungen'  # noqa

    class Meta:
        verbose_name_plural = 'Globale Einstellung'
        verbose_name = 'Globale Einstellung'


class AppPromotion(models.Model):
    ios_app_link = models.CharField(
        max_length=500,
        blank=True,
        default=''
    )
    android_app_link = models.CharField(
        max_length=500,
        blank=True,
        default=''
    )

    def __str__(self):
        return self.android_app_link or self.ios_app_link


class HeaderMenu(models.Model):
    link = models.CharField(
        max_length=500,
        default='',
        blank=True
    )
    link_text = models.CharField(
        max_length=100,
        default='',
        blank=True
    )

    class Meta:
        verbose_name_plural = 'Header-Menü'
        verbose_name = 'Header-Menü'

    def __str__(self):
        return self.link_text


class RecommendedBy(models.Model):
    logo = models.FileField(
        upload_to='project/recommended_by/',
        help_text='Ja: PNG, JPG, JPEG, SVG... Nein: PDF, MP4 und alles was kein Logo sein kann.'  # noqa
    )
    link = models.CharField(
        max_length=500,
        default='',
        blank=True
    )

    class Meta:
        verbose_name_plural = 'Empfohlen von (im Header)'
        verbose_name = 'Empfohlen von (im Header)'

    def __str__(self):
        return self.link


class MenuChild(models.Model):
    menu = models.ForeignKey(
        HeaderMenu,
        on_delete=models.SET_NULL,
        null=True
    )
    link = models.CharField(
        max_length=500,
        default='',
        blank=True
    )
    link_text = models.CharField(
        max_length=100,
        default='',
        blank=True
    )

    class Meta:
        verbose_name_plural = 'Header Sub-Menü'
        verbose_name = 'Header Sub-Menü'

    def __str__(self):
        return '[Submenu] %s' % self.link_text


class FooterColumn(models.Model):
    header = models.CharField(
        max_length=100,
        default='',
        blank=True
    )

    class Meta:
        verbose_name_plural = 'Footer Spalte'
        verbose_name = 'Footer Spalte'

    def __str__(self):
        return self.header


class FooterRow(models.Model):
    column = models.ForeignKey(
        FooterColumn,
        related_name='rows',
        on_delete=models.SET_NULL,
        null=True
    )
    link = models.CharField(
        max_length=500,
        default='',
        blank=True
    )
    link_text = models.CharField(
        max_length=100,
        default='',
        blank=True
    )
    open_new_tab = models.BooleanField(default=False)
    image = models.ImageField(
        upload_to='footer_img/',
        blank=True,
        default=''
    )

    class Meta:
        verbose_name_plural = 'Footer Reihe'
        verbose_name = 'Footer Reihe'

    def __str__(self):
        return 'Row von %s' % self.column.header


class SEO(models.Model):
    title = models.CharField(
        max_length=200,
        default='mathefragen.de - Fragen. Teilen. Helfen.',
        blank=True
    )
    meta_description = models.CharField(
        max_length=200,
        default='Wo Schüler & Studenten Mathe verstehen.',
        blank=True
    )
    share_image = models.ImageField(
        default='',
        blank=True,
        upload_to='project/share-img/'
    )
    fb_app_id = models.CharField(
        max_length=100,
        default='359857967960662',
        blank=True,
        help_text='Facebook App ID'
    )

    class Meta:
        verbose_name_plural = 'SEO'
        verbose_name = 'SEO'

    def __str__(self):
        return self.title


class Performance(models.Model):
    feed_3_days = models.BooleanField(
        default=True,
        help_text='Hauptfeed zeigt nur Content der letzten 3 Tage'
    )

    class Meta:
        verbose_name_plural = 'Performance Settings'
        verbose_name = 'Performance Settings'


class Snippet(models.Model):
    name = models.CharField(
        max_length=50
    )
    embed_code = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Code Snippets (e.g. Google Analytics)'
        verbose_name = 'Code Snippets (e.g. Google Analytics)'

    def __str__(self):
        return self.name
