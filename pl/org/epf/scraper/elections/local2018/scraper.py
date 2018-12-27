import scrapy


def extract_all_text(elem):
    return ' '.join([t.strip() for t in elem.css('::text').extract()])


class Spider(scrapy.Spider):
    name = 'elections-pl-2018'
    # start_urls = ['https://wybory2018.pkw.gov.pl/pl/obwody']

    # Testing
    def start_requests(self):
        yield scrapy.Request(url='https://wybory2018.pkw.gov.pl/pl/obwody/140000', callback=self.parse_wojewodztwo)

    def parse(self, response):
        for region in response.css('.stat_table.stat_table_dt tbody a'):
            title = region.css('::text').extract_first()
            link = region.css('::attr(href)').extract_first()
            # Teryt is a unique identification number for administrative boundaries
            teryt = int(link.split('/')[-1])

            yield {'type': 'wojewodztwo', 'title': title,
                   'link': link,  # TODO compact
                   'teryt': teryt}
            yield response.follow(link, self.parse_wojewodztwo)

    def parse_wojewodztwo(self, response):
        teryt_parent = int(response.url.split('/')[-1])
        for region in response.css('.stat_table.stat_table_dt tbody a'):
            title = region.css('::text').extract_first()
            link = region.css('::attr(href)').extract_first()
            teryt = int(link.split('/')[-1])

            yield {'type': 'powiat', 'title': title,
                   'link': link,  # TODO compact
                   'teryt': teryt, 'teryt_parent': teryt_parent}
            yield response.follow(link, self.parse_powiat)

    def parse_powiat(self, response):
        header = response.css('.page_header h2 ::text').extract_first()
        # Miasto na prawach powiatu (it's both gmina and powiat)
        if header == 'Obwody':
            teryt = int(response.url.split('/')[-1])
            for district in response.css('.stat_table.stat_table_dt tbody tr'):
                fields = district.css('td')

                def is_accessible(x):
                    try:
                        return {
                            'Tak': True,
                            'Nie': False
                        }.get(x)
                    except KeyError:
                        self.logger.warn("Niepoprawna wartość dostępności dla os. z niepełnosprawnoścami: " + x)
                        return None

                d = dict(
                    type='district',
                    teryt_parent=teryt,
                    number=extract_all_text(fields[0]),
                    place=extract_all_text(fields[1]),
                    # district_type: stały, szpital, dom pomocy społecznej, zakład karny, areszt śledczy,
                    #  oddział zewnętrzny aresztu śledczego, oddział zewnętrzny zakładu karnego
                    # district_type=extract_all_text(fields[2]), # TODO smaller output

                    accessible=is_accessible(extract_all_text(fields[3])),
                    # coverage=extract_all_text(fields[4]) # TODO smaller output
                )
                yield d
        #
        # else:
        #     teryt_parent = int(response.url.split('/')[-1])
        #     for region in response.css('.stat_table.stat_table_dt tbody a'):
        #         title = region.css('::text').extract_first()
        #         link = region.css('::attr(href)').extract_first()
        #         teryt = int(link.split('/')[-1])
        #
        #         yield {'type': 'gmina', 'title': title,
        #                'link': link, # TODO compact
        #                'teryt': teryt, 'teryt_parent': teryt_parent}
        #         yield response.follow(link, self.parse_electoral_districts)

    '''
    Finally we get electoral districts
    '''
    def parse_electoral_districts(self, response):
        teryt = int(response.url.split('/')[-1])
        for district in response.css('.stat_table.stat_table_dt tbody tr'):
            fields = district.css('td')

            def is_accessible(x):
                try:
                    return {
                        'Tak': True,
                        'Nie': False
                    }.get(x)
                except KeyError:
                    self.logger.warn("Niepoprawna wartość dostępności dla os. z niepełnosprawnoścami: " + x)
                    return None

            d = dict(
                type='district',
                teryt_parent=teryt,
                number=extract_all_text(fields[0]),
                place=extract_all_text(fields[1]),
                # district_type: stały, szpital, dom pomocy społecznej, zakład karny, areszt śledczy,
                #  oddział zewnętrzny aresztu śledczego, oddział zewnętrzny zakładu karnego
                # district_type=extract_all_text(fields[2]), # TODO smaller output

                accessible=is_accessible(extract_all_text(fields[3])),
                # coverage=extract_all_text(fields[4]) # TODO smaller output
            )

            # TODO smaller output
            # try:
            #     pos = d['place'].index(',')
            #     d['place_name'] = d['place'][0:pos].strip('()')
            #     d['place_address'] = d['place'][pos + 1:].strip()
            #
            #     m = re.search('\d+', d['place_address'])
            #     if m:
            #         d['place_address_street'] = d['place_address'][:m.start()].strip()
            #         d['place_address_number'] = d['place_address'][m.start():m.end()]
            #         d['place_address_city'] = d['place_address'][m.end():].strip()
            #
            # except ValueError:
            #     pass
            
            yield d
