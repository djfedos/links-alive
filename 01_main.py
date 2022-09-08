from bs4 import BeautifulSoup
import httpx
from pathlib import Path

# discovered_links = set()
# valid_links = set()
# invalid_links = set()


def extract_links(webpage, site_address, discovered_links):
    # headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'}
    local_discovered_links = set()
    req = httpx.get(webpage)

    soup = BeautifulSoup(req.text, 'lxml')
    anchors = soup.find_all('a')

    for a in anchors:
        link = a.attrs.get('href')

        if link.startswith('https://') or link.startswith('http://'):
            pass
        elif link == '.' or link == '/' :
            link = None
        elif link.startswith('../../../'):
            link = site_address + '/' + link[9:]
        elif link.startswith('../../'):
            link = site_address + '/' + link[6:]
        elif link.startswith('../'):
            link = site_address + '/' + link[3:]
        elif link.startswith('#'):
            link = site_address + '/' + link
        else:
            link = webpage + '/' + link

        if link and (link not in discovered_links):
            local_discovered_links.add(link)
            print(f'Added {link} to local_discovered_links')

    return local_discovered_links


def check_links(link_set):
    valid_links = set()
    invalid_links = set()
    for link in link_set:
        if link not in valid_links and link not in invalid_links:
            try:
                req_link = httpx.get(link)
                if req_link.status_code == 200:
                    valid_links.add(link)
                    print(f'Added {link} to valid links')
                else:
                    invalid_links.add(link)
                    print(f'Added {link} to invalid links')
            except httpx.RemoteProtocolError:
                invalid_links.add(link)
    return valid_links, invalid_links


def output_files(valid_links, invalid_links):
    # Path('out').absolute().parent.mkdir(exist_ok=True, parents=True)
    with open('valid_links.txt', 'a') as valid:
        for link in valid_links:
            valid.write(link)
            valid.write('\n')

    with open('invalid_links.txt', 'a') as invalid:
        for link in invalid_links:
            invalid.write(link)
            invalid.write('\n')


def crawl(site_address):
    discovered_links = set()
    just_discovered = extract_links(site_address, site_address, set())
    valid_links, invalid_links = check_links(just_discovered)
    while just_discovered:
        just_validated_links = set()
        just_invalidated_links = set()
        for link in valid_links:
            discovered_links |= just_discovered
            if link.startswith(site_address):
                print(f'Crawling {link}')
                just_discovered = extract_links(link, site_address, discovered_links)
                print(f'{link} processed')
            print('Updated discovered links')
            val, inval = check_links(just_discovered)
            just_validated_links |= val
            just_invalidated_links |= inval
        valid_links |= just_validated_links
        invalid_links |= just_invalidated_links


    output_files(valid_links=valid_links, invalid_links=invalid_links)


if __name__ == '__main__':
    crawl('https://yairdar.github.io')


