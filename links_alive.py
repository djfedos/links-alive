from bs4 import BeautifulSoup
import httpx
from urllib.parse import urljoin, urlparse
import logging
import fire
from collections import deque

logging.basicConfig(filename='invalid.log', filemode='w', format='%(asctime)s - %(message)s', level=logging.INFO)


class Page:
    def __init__(self, address: str):
        self.address = address
        self.valid_links = set()
        self.invalid_links = set()


class Link:
    def __init__(self, page_of_origin: Page, link_url: str):
        self.page_of_origin = page_of_origin
        # link.url is a unique property to store in sets
        self.url = urljoin(page_of_origin.address, link_url)
        self.url_parsed = urlparse(self.url)
        self.website = self.url_parsed.scheme + '://' + self.url_parsed.netloc
        self.stripped_url = self.website + self.url_parsed.path


class Explorer:
    # add discovered web pages of the site to this queue
    unexplored = deque()
    # add explored page.address to this set
    explored = set()
    # links to validate
    unvalidated = deque()
    website = None

    @classmethod
    def set_website(cls, website):
        Explorer.website = website

    def __init__(self, webpage: Page):
        self.webpage = webpage

    def discover_links(self):
        req = httpx.get(self.webpage.address)

        soup = BeautifulSoup(req.text, 'lxml')
        anchors = soup.find_all('a')

        for a in anchors:
            link_url = a.attrs.get('href')

            if not link_url:
                pass
            elif link_url == '.' or link_url == '/':
                link_url = None
            else:
                link_url = urljoin(self.webpage.address, link_url)

            if link_url:
                link = Link(page_of_origin=self.webpage, link_url=link_url)
                Explorer.unvalidated.append(link)
                if link.website == Explorer.website:
                    if link.stripped_url not in self.explored:
                        Explorer.unexplored.append(link)

        Explorer.explored.add(self.webpage)
        print(f'Added {link_url} to local_discovered_links')




class Validator:
    # class-wide variables store all the valid and invalid links that are found at the moment
    valid = set()
    invalid = set()

    def __init__(self, link):
        self.link = link

    def validate_link(self):

        def add_invalid(inv_message):
            # Add link to global (Validator class-wide) valid link storage
            Validator.invalid.add(self.link.url)
            # Add link to local (Page instance-wide) valid link storage
            self.link.page_of_origin.invalid_links.add(self.link)
            print(inv_message)
            logging.info(inv_message)

        if self.link.url in Validator.valid:
            print(f'Link {self.link.url} on the {self.link.page_of_origin} page is valid')
            self.link.page_of_origin.valid_links.add(self.link)
        elif self.link.url in Validator.invalid:
            inv_message = f'Link {self.link.url} on the {self.link.page_of_origin} page is invalid'
            print(inv_message)
            logging.info(inv_message)
            self.link.page_of_origin.invalid_links.add(self.link)

        try:
            # check stripped URL to avoid false positive invalidation
            req_link = httpx.get(self.link.stripped_url)
            # TODO: separate algorithm for redirect validation
            if req_link.is_success or req_link.is_redirect:
                print(f'Link {self.link.url} on the {self.link.page_of_origin} page is valid')
                # Add link to global (Validator class-wide) valid link storage
                Validator.valid.add(self.link.url)
                # Add link to local (Page instance-wide) valid link storage
                self.link.page_of_origin.valid_links.add(self.link)
            else:
                inv_message = f'Link {self.link.url} on the {self.link.page_of_origin} page is invalid'
                add_invalid(inv_message=inv_message)

        except httpx.RemoteProtocolError:
            inv_message = f'RemoteProtocolError, {self.link.url} on the {self.link.page_of_origin} page is invalid'
            add_invalid(inv_message=inv_message)
        except httpx.UnsupportedProtocol:
            inv_message = f'UnsupportedProtocol, {self.link.url} on the {self.link.page_of_origin} page is invalid'
            add_invalid(inv_message=inv_message)
        except httpx.ConnectError:
            inv_message = f'ConnectError [SSL: CERTIFICATE_VERIFY_FAILED], {self.link.url} on the {self.link.page_of_origin} page is invalid'
            add_invalid(inv_message=inv_message)
        except httpx.ConnectTimeout:
            inv_message = f'ConnectTimeout, {self.link.url} on the {self.link.page_of_origin} page is invalid'
            add_invalid(inv_message=inv_message)
        except httpx.ReadTimeout:
            inv_message = f'ReadTimeout, {self.link.url} on the {self.link.page_of_origin} page is invalid'
            add_invalid(inv_message=inv_message)


if __name__ == '__main__':
    fire.Fire(crawl)
