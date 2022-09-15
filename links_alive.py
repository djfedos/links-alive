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
    def init_website(cls, website):
        Explorer.website = website
        Explorer.unexplored.append(Page(website))
        Explorer.loop()
        Validator.loop()


    @classmethod
    def output_logs(cls):
        counter = 0
        for page in Explorer.explored:
            counter += 1
            with open(f'page_{counter}.log', 'w') as page_log:
                page_log.write(f'{page.address} \n')
                page_log.write(f'Invalid links: \n')
                for invalid_link in page.invalid_links:
                    page_log.write(f'{invalid_link.url}, \n')
                page_log.write(f'Valid links: \n')
                for valid_link in page.valid_links:
                    page_log.write(f'{valid_link.url} \n')

    # process website pages sequentially
    @classmethod
    def loop(cls):
        while Explorer.unexplored:
            e = Explorer(Explorer.unexplored.popleft())
            e.discover_links()
        # when no unexplored pages left, we add a marker to the end of the links queue to break out of validation loop
        Explorer.unvalidated.append(NotImplemented)

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
                    if link.stripped_url not in Explorer.explored and link.stripped_url != self.webpage.address:
                        Explorer.unexplored.append(Page(link.stripped_url))

        Explorer.explored.add(self.webpage)
        print(f'Added {self.webpage.address} to explored')


class Validator:
    # class-wide variables store all the valid and invalid links that are found at the moment
    valid = set()
    invalid = set()

    def __init__(self, link):
        self.link = link

    @classmethod
    def output_logs(cls):
        with open('valid_links.log', 'w') as valid:
            for link in Validator.valid:
                valid.write(link)
                valid.write('\n')
        with open('invalid_links.log', 'w') as invalid:
            for link in Validator.invalid:
                invalid.write(link)
                invalid.write('\n')

    @classmethod
    def loop(cls):
        while True:
            v = Validator(Explorer.unvalidated.popleft())
            if v.link is NotImplemented:
                break
            v.validate_link()
        Validator.output_logs()
        Explorer.output_logs()

    def validate_link(self):

        def add_invalid(inv_message):
            # Add link to global (Validator class-wide) valid link storage
            Validator.invalid.add(self.link.url)
            # Add link to local (Page instance-wide) valid link storage
            self.link.page_of_origin.invalid_links.add(self.link)
            print(inv_message)
            logging.info(inv_message)

        if self.link.url in Validator.valid:
            print(f'Link {self.link.url} on the {self.link.page_of_origin.address} page is valid')
            self.link.page_of_origin.valid_links.add(self.link)
        elif self.link.url in Validator.invalid:
            inv_message = f'Link {self.link.url} on the {self.link.page_of_origin.address} page is invalid'
            print(inv_message)
            logging.info(inv_message)
            self.link.page_of_origin.invalid_links.add(self.link)

        try:
            # check stripped URL to avoid false positive invalidation
            req_link = httpx.get(self.link.stripped_url)
            # TODO: separate algorithm for redirect validation
            if req_link.is_success or req_link.is_redirect:
                print(f'Link {self.link.url} on the {self.link.page_of_origin.address} page is valid')
                # Add link to global (Validator class-wide) valid link storage
                Validator.valid.add(self.link.url)
                # Add link to local (Page instance-wide) valid link storage
                self.link.page_of_origin.valid_links.add(self.link)
            else:
                inv_message = f'Link {self.link.url} on the {self.link.page_of_origin.address} page is invalid'
                add_invalid(inv_message=inv_message)

        except httpx.RemoteProtocolError:
            inv_message = f'RemoteProtocolError, {self.link.url} on the {self.link.page_of_origin.address} page is invalid'
            add_invalid(inv_message=inv_message)
        except httpx.UnsupportedProtocol:
            inv_message = f'UnsupportedProtocol, {self.link.url} on the {self.liself.link.page_of_originnk.page_of_origin.address} page is invalid'
            add_invalid(inv_message=inv_message)
        except httpx.ConnectError:
            inv_message = f'ConnectError [SSL: CERTIFICATE_VERIFY_FAILED], {self.link.url} on the {self.link.page_of_origin.address} page is invalid'
            add_invalid(inv_message=inv_message)
        except httpx.ConnectTimeout:
            inv_message = f'ConnectTimeout, {self.link.url} on the {self.link.page_of_origin.address} page is invalid'
            add_invalid(inv_message=inv_message)
        except httpx.ReadTimeout:
            inv_message = f'ReadTimeout, {self.link.url} on the {self.link.page_of_origin.address} page is invalid'
            add_invalid(inv_message=inv_message)


if __name__ == '__main__':
    fire.Fire(Explorer.init_website)
