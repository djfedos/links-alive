from bs4 import BeautifulSoup
import httpx
from urllib.parse import urljoin
import logging
import fire

logging.basicConfig(filename='invalid.log', filemode='w', format='%(asctime)s - %(message)s', level=logging.INFO)


def extract_links(webpage):

    local_discovered_links = set()
    req = httpx.get(webpage)

    soup = BeautifulSoup(req.text, 'lxml')
    anchors = soup.find_all('a')

    for a in anchors:
        link = a.attrs.get('href')

        if not link:
            pass
        elif link == '.' or link == '/':
            link = None
        else:
            link = urljoin(webpage, link)

        if link:
            local_discovered_links.add(link)
            print(f'Added {link} to local_discovered_links')

    return local_discovered_links


def validate_link(link):
    try:
        req_link = httpx.get(link)
        if req_link.is_success or req_link.is_redirect:
            print(f'Link {link} is valid')
            return True
        else:
            inv_message = f'Link {link} is invalid'
            print(inv_message)
            logging.info(inv_message)
            return False

    except httpx.RemoteProtocolError:
        inv_message = f'RemoteProtocolError, {link} is considered invalid'
        print(inv_message)
        logging.info(inv_message)
        return False
    except httpx.UnsupportedProtocol:
        inv_message = f'UnsupportedProtocol, {link} is considered invalid'
        print(inv_message)
        logging.info(inv_message)
        return False
    except httpx.ConnectError:
        inv_message = f'ConnectError [SSL: CERTIFICATE_VERIFY_FAILED], {link} is considered invalid'
        print(inv_message)
        logging.info(inv_message)
        return False
    except httpx.ConnectTimeout:
        inv_message = f'ConnectTimeout, {link} is considered invalid'
        print(inv_message)
        logging.info(inv_message)
        return False
    except httpx.ReadTimeout:
        inv_message = f'ReadTimeout, {link} is considered invalid'
        print(inv_message)
        logging.info(inv_message)
        print(f'ReadTimeout, {link} is considered invalid')
        return False


def crawl(site_address=''):
    if not site_address:
        print('Usage: python links_alive.py [SITE_ADDRESS]')
        print('E.g.: python links_alive.py "https://djfedos.github.io"')
        return False
    discovered_links = set()
    discovered_links.add(site_address)
    valid_links = set()
    invalid_links = set()
    to_be_validated = discovered_links
    left_to_validate = 1
    while to_be_validated:
        print('Validation loop started')
        validated_in_current_loop = set()
        for link in to_be_validated:
            if validate_link(link):
                validated_in_current_loop.add(link)
                with open('valid.log', 'a') as val_log:
                    val_log.write(link + '\n')
            else:
                invalid_links.add(link)
            left_to_validate -= 1
            print(f'{left_to_validate} left to validate in this loop')
        valid_links |= validated_in_current_loop
        print('Update valid_links')

        for link in validated_in_current_loop:
            if link.startswith(site_address):
                print(f'Extracting links from {link}...')
                discovered_links |= extract_links(link)
                print('Update discovered_links')
        to_be_validated = discovered_links - valid_links - invalid_links
        left_to_validate = len(to_be_validated)
        print(f'{len(to_be_validated)} links to be validated now')
        print(f'{len(valid_links)} links are valid')
        print(f'{len(invalid_links)} links are invalid')
        print(f'{len(discovered_links)} links are discovered')

    print('Crawling complete')
    return True


if __name__ == '__main__':
    fire.Fire(crawl)
