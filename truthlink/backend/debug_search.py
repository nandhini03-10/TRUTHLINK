from truthlink.services.source_discovery import search_duckduckgo, search_bing, discover_sources_for_query

q = 'thalaivar 173 is produced by rkfi'
print('Query:', q)

print('\nDuckDuckGo results:')
for url, title in search_duckduckgo(q, limit=10):
    print('-', title, url)

print('\nBing results:')
for url, title in search_bing(q, limit=10):
    print('-', title, url)

print('\nDiscover sources:')
for url, title, kind, authority in discover_sources_for_query(q):
    print('-', kind, authority, title, url)
