# Copyright (c) 2014-2021 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from gettext import gettext as _
import json
from locale import getdefaultlocale

from lollypop.define import App
from lollypop.utils import escape
from lollypop.logger import Logger


class WikipediaHelper:
    """
        Helper for wikipedia search
    """

    __API_SEARCH = "https://%s.wikipedia.org/w/api.php?action=query" +\
        "&list=search&srsearch=%s&format=json"
    __API_INFO = "https://%s.wikipedia.org/w/api.php?action=query" +\
        "&pageids=%s&format=json" +\
        "&prop=extracts&exlimit=max&explaintext&redirects=1"

    def __init__(self):
        """
            Init wikipedia
        """
        self.__locale = getdefaultlocale()[0][0:2]

    def get_content_for_term(self, term):
        """
            Get content for term
            @param term as str
            @return bytes/None
        """
        try:
            (locale, page_id) = self.__search_term(term)
            if page_id is None:
                return None
            uri = self.__API_INFO % (locale, page_id)
            (status, data) = App().task_helper.load_uri_content_sync(uri)
            if status:
                decode = json.loads(data.decode("utf-8"))
                extract = decode["query"]["pages"][str(page_id)]["extract"]
                return extract.encode("utf-8")
        except Exception as e:
            Logger.error("Wikipedia::get_content_for_term(): %s", e)
        return None

    def get_content_for_page_id(self, page_id, locale):
        """
            Get page content
            @param page_id as str
            @param locale as str
            @return bytes/None
        """
        try:
            uri = self.__API_INFO % (locale, page_id)
            (status, data) = App().task_helper.load_uri_content_sync(uri)
            if status:
                decode = json.loads(data.decode("utf-8"))
                extract = decode["query"]["pages"][str(page_id)]["extract"]
                return extract.encode("utf-8")
        except Exception as e:
            Logger.error("Wikipedia::get_content_for_page_id(): %s", e)
        return None

    def get_search_list(self, term):
        """
            Get search list for term
            @param term as str
            @return [(str, str)]: list of locales/title
        """
        pages = []
        try:
            for locale in [self.__locale, "en"]:
                uri = self.__API_SEARCH % (locale, term)
                (status, data) = App().task_helper.load_uri_content_sync(uri)
                decode = json.loads(data.decode("utf-8"))
                if status:
                    for item in decode["query"]["search"]:
                        pages.append((locale, item["title"], item["pageid"]))
        except Exception as e:
            print("Wikipedia::get_search_list(): %s", e)
        return pages

#######################
# PRIVATE             #
#######################
    def __search_term(self, term):
        """
            Search term on Wikipdia
            @param term as str
            @return pageid as str
        """
        try:
            for locale in [self.__locale, "en"]:
                uri = self.__API_SEARCH % (locale, term)
                (status, data) = App().task_helper.load_uri_content_sync(uri)
                if status:
                    decode = json.loads(data.decode("utf-8"))
                    for item in decode["query"]["search"]:
                        if escape(item["title"].lower()) ==\
                                escape(term.lower()):
                            return (locale, item["pageid"])
                        else:
                            for word in [_("band"), _("singer"),
                                         "band", "singer"]:
                                if item["snippet"].lower().find(word) != -1:
                                    return (locale, item["pageid"])
        except Exception as e:
            print("Wikipedia::__search_term(): %s", e)
        return ("", None)
