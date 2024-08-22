import base64
import logging
import re
import threading
from io import BytesIO

import boto3
import piexif
import requests
from PIL import Image, ExifTags
from django.conf import settings
from django.contrib.auth.hashers import get_hasher
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from pytz import timezone as pytz_timezone
from requests.exceptions import MissingSchema

from mathefragen.apps.core.models import create_default_hash

logger = logging.getLogger(__name__)

hasher = get_hasher('phpass')


class EmailThread(threading.Thread):
    def __init__(self, subject, recipient_list, template_name, **data):
        self.subject = subject
        self.recipient_list = recipient_list
        self.template_name = template_name
        self.data = data
        self.data.update({
            'subject': self.subject,
            'domain': settings.DOMAIN
        })
        self.html_content = render_to_string(self.template_name, self.data)
        text_content = strip_tags(self.html_content)
        self.text_content = text_content

        threading.Thread.__init__(self)

    def run(self):
        msg = EmailMultiAlternatives(
            self.subject,
            self.text_content,
            '%s - <no-reply@%s>' % (
                settings.DOMAIN.replace('localhost:8000', 'mathefragen.de'),
                settings.DOMAIN.replace('www.', '').replace('localhost:8000', 'mathefragen.de')
            ),
            self.recipient_list
        )
        msg.attach_alternative(self.html_content, "text/html")
        # send emails only in production
        msg.send()


def send_email_in_template(subject, recipient_list, **data):
    template_name = 'email/template.html'
    EmailThread(subject, recipient_list, template_name, **data).start()


def generate_cool_number(value, num_decimals=2):
    if not value:
        return 0

    int_value = int(value)
    formatted_number = '{{:.{}f}}'.format(num_decimals)
    if int_value < 1000:
        return str(int_value)
    elif int_value < 1000000:
        final_cool_number = formatted_number.format(int_value / 1000.0).rstrip('0.') + 'K'
    else:
        final_cool_number = formatted_number.format(int_value / 1000000.0).rstrip('0.') + 'M'

    return final_cool_number


def convert_base64_to_image(base64_text):
    date_folder = '%s/%s/%s/' % (
        timezone.now().year, timezone.now().month, timezone.now().day
    )
    image_path = date_folder

    random_image_file_name = create_default_hash()
    final_path = '%s%s.png' % (
        image_path, random_image_file_name
    )

    if isinstance(base64_text, str):
        base64_text = base64_text.encode('utf-8')

    base64_text_without_meta = base64_text.split(b'base64,')[1]

    with open(final_path, "wb") as fh:
        fh.write(base64.decodebytes(base64_text_without_meta))

    return final_path


def use_mobile_images(text):
    def _change_img_url(path):
        path = re.sub('(height=".*?")', '', path)
        path = re.sub('(width=".*?")', 'width="580" height="auto"', path)
        if 'width="580"' not in path:
            path = re.sub('src="(.*?)"', lambda x: '%s width="580" height="auto"' % x.group(), path)
        path = re.sub('class="fit_width"', '', path)
        return path

    return re.sub('<img.*?src="(.*?)"[^>]+>', lambda x: _change_img_url(x.group()), text)


def convert_img_base64_to_html_tag(text):
    """
    replaces [img]base64[/img] with <img src='url' class="fit_width">
    """
    pattern = r"\[img](.*?)\[/img]"

    dict_to_replace = dict()
    matches = re.findall(pattern, text)
    for match in matches:
        img_url = convert_base64_to_image(match)
        img_url = '/media%s' % img_url.split('media')[1]
        dict_to_replace[match] = '<img src="%s" class="fit_width" />' % img_url

    for img_base64, img_url in dict_to_replace.items():
        text = text.replace(img_base64, img_url)

    text = text.replace('[img]', '').replace('[/img]', '')

    return text


class RepairImages(threading.Thread):
    """
    it runs as thread and does not block the flow
    """

    def __init__(self, text='', img_url=''):
        self.text = text
        self.img_url = img_url
        threading.Thread.__init__(self)

    def run(self):
        if self.img_url:
            self.repair_image_rotation(self.img_url)
        else:
            pattern = r'src="(.*?)"'
            image_urls = re.findall(pattern, self.text)
            for img_url in image_urls:
                # fix answer uploads
                self.repair_image_rotation(img_url)

    @staticmethod
    def rotate_jpeg(img_url):
        response = requests.get(img_url)
        img = Image.open(BytesIO(response.content))
        if "exif" in img.info:
            exif_dict = piexif.load(img.info["exif"])

            if piexif.ImageIFD.Orientation in exif_dict["0th"]:
                orientation = exif_dict["0th"].pop(piexif.ImageIFD.Orientation)
                exif_bytes = piexif.dump(exif_dict)

                if orientation == 2:
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 3:
                    img = img.rotate(180)
                elif orientation == 4:
                    img = img.rotate(180).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 5:
                    img = img.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 6:
                    img = img.rotate(-90, expand=True)
                elif orientation == 7:
                    img = img.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)

                in_mem_file = BytesIO()
                img.save(in_mem_file, exif=exif_bytes, format=img.format)
                in_mem_file.seek(0)

                s3 = boto3.client('s3')
                s3.upload_fileobj(
                    in_mem_file,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    settings.AWS_ACCESS_KEY_ID
                )

    @staticmethod
    def repair_image_rotation(img_url):
        absolute_url = img_url
        try:
            response = requests.get(absolute_url)
            image = Image.open(BytesIO(response.content))

            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break

            exif = dict(image._getexif().items())

            if exif[orientation] == 3:
                image = image.transpose(Image.ROTATE_180)
            elif exif[orientation] == 6:
                image = image.transpose(Image.ROTATE_270)
            elif exif[orientation] == 8:
                image = image.transpose(Image.ROTATE_90)

            in_mem_file = BytesIO()
            image.save(in_mem_file, format=image.format)
            in_mem_file.seek(0)

            s3 = boto3.client('s3')
            s3.upload_fileobj(
                in_mem_file,
                settings.AWS_STORAGE_BUCKET_NAME,
                settings.AWS_ACCESS_KEY_ID
            )

        except (AttributeError, KeyError, IndexError, MissingSchema) as e:
            # cases: image don't have getexif
            pass


def utcisoformat(dt):
    """
    Return a datetime object in ISO 8601 format in UTC, without microseconds
    or time zone offset other than 'Z', e.g. '2011-06-28T00:00:00Z'. Useful
    for making Django DateTimeField values compatible with the
    jquery.localtime plugin.
    """
    # A pytz.timezone object representing the Django project time zone
    # Use TZ.localize(mydate) instead of tzinfo=TZ to ensure that DST rules
    # are respected
    tz = pytz_timezone(settings.TIME_ZONE)

    # Convert datetime to UTC, remove microseconds, remove timezone, convert to string
    return tz.localize(dt.replace(microsecond=0)).replace(tzinfo=None).isoformat() + 'Z'
