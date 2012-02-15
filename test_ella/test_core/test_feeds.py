# -*- coding: utf-8 -*-
from PIL import Image

from django.test import TestCase

from nose import tools, SkipTest

from django.core.urlresolvers import reverse
from django.http import HttpRequest

from ella.core.models import Listing
from ella.core.feeds import RSSTopCategoryListings
from ella.photos.models import Photo, Format

from test_ella.test_core import create_basic_categories, \
        create_and_place_more_publishables, list_all_publishables_in_category_by_hour

class TestFeeds(TestCase):

    def setUp(self):
        try:
            import feedparser
        except ImportError:
            raise SkipTest()

        super(TestFeeds, self).setUp()
        create_basic_categories(self)
        create_and_place_more_publishables(self)
        list_all_publishables_in_category_by_hour(self)


        self._feeder = RSSTopCategoryListings('test', HttpRequest())

    def _set_photo(self):
        from test_ella.test_photos.fixtures import create_photo

        photo = create_photo(self)

        self.publishables[0].photo = photo
        self.publishables[0].save()
        # update the cache on the Listing object
        self.listings[0].publishable = self.publishables[0]

    def test_rss(self):
        import feedparser
        Listing.objects.all().update(category=self.category)
        url = reverse('feeds', kwargs={'url':'rss'})
        c = self.client

        response = c.get(url)
        tools.assert_equals(200, response.status_code)
        d = feedparser.parse(response.content)

        tools.assert_equals(len(self.publishables), len(d['items']))

    def test_atom(self):
        import feedparser
        Listing.objects.all().update(category=self.category)
        url = reverse('feeds', kwargs={'url':'atom'})
        c = self.client

        response = c.get(url)
        tools.assert_equals(200, response.status_code)
        d = feedparser.parse(response.content)

        tools.assert_equals(len(self.publishables), len(d['items']))

    def test_title_defaults_to_category_title(self):
        tools.assert_true(self._feeder.title(self.category), self.category.title)

    def test_title_uses_app_data_when_set(self):
        self.category.app_data = {'syndication': {'title': 'SYNDICATION_TITLE'}}
        tools.assert_true(self._feeder.title(self.category), 'SYNDICATION_TITLE')

    def test_description_defaults_to_category_title(self):
        tools.assert_true(self._feeder.title(self.category), self.category.title)

    def test_description_uses_app_data_when_set(self):
        self.category.app_data = {'syndication': {'description': 'SYNDICATION_DESCRIPTION'}}
        tools.assert_true(self._feeder.description(self.category), 'SYNDICATION_DESCRIPTION')

    def test_get_enclosure_uses_original_when_format_not_set(self):
        self._set_photo()
        tools.assert_true(self.publishables[0].photo is not None)
        original = self.publishables[0].photo.get_image_info()
        new = self._feeder.get_enclosure_image(self.listings[0], enc_format=None)
        tools.assert_equals(original, new)

    def test_get_enclosure_uses_original_when_format_not_found(self):
        non_existent_format_name = 'aaa'
        self._set_photo()
        tools.assert_true(self.publishables[0].photo is not None)
        original = self.publishables[0].photo.get_image_info()
        new = self._feeder.get_enclosure_image(self.listings[0], enc_format=non_existent_format_name)
        tools.assert_equals(original, new)

    def test_get_enclosure_uses_formated_photo_when_format_available(self):
        existent_format_name = 'enc_format'
        f = Format.objects.create(name=existent_format_name, max_width=10, max_height=10,
            flexible_height=False, stretch=False, nocrop=False)
        f.sites = [self.site_id]

        self._set_photo()
        tools.assert_true(self.publishables[0].photo is not None)
        original = self.publishables[0].photo.image
        new = self._feeder.get_enclosure_image(self.listings[0], enc_format=existent_format_name)
        tools.assert_not_equals(unicode(original), unicode(new))

    def test_get_enclosure_returns_none_when_no_image_set(self):
        tools.assert_equals(self._feeder.get_enclosure_image(self.listings[0]), None)




