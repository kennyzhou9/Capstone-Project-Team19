# -*- coding: utf-8 -*-
from googlemaps import GoogleMapsScraper
from datetime import datetime, timedelta
import argparse
import csv
from termcolor import colored
import time


ind = {'most_relevant' : 0 , 'newest' : 1, 'highest_rating' : 2, 'lowest_rating' : 3 }
HEADER = ['id_review', 'caption', 'relative_date', 'retrieval_date', 'rating', 'username', 'n_review_user', 'n_photo_user', 'url_user','address']
HEADER_W_SOURCE = ['id_review', 'caption', 'relative_date','retrieval_date', 'rating', 'username', 'n_review_user', 'n_photo_user', 'url_user', 'url_source','address']

def csv_writer(source_field, ind_sort_by, path='data_costco/'):
    outfile= ind_sort_by + '_gm_reviews.csv'
    targetfile = open(path + outfile, mode='w', encoding='utf-8', newline='\n')
    writer = csv.writer(targetfile, quoting=csv.QUOTE_MINIMAL)

    if source_field:
        h = HEADER_W_SOURCE
    else:
        h = HEADER
    writer.writerow(h)

    return writer


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Google Maps reviews scraper.')
    parser.add_argument('--N', type=int, default=100, help='Number of reviews to scrape')
    parser.add_argument('--i', type=str, default='urls.txt', help='target URLs file')
    parser.add_argument('--sort_by', type=str, default='newest', help='sort by most_relevant, newest, highest_rating or lowest_rating')
    parser.add_argument('--place', dest='place', action='store_true', help='Scrape place metadata')
    parser.add_argument('--debug', dest='debug', action='store_true', help='Run scraper using browser graphical interface')
    parser.add_argument('--source', dest='source', action='store_true', help='Add source url to CSV file (for multiple urls in a single file)')
    parser.set_defaults(place=False, debug=False, source=True)

    args = parser.parse_args()

    # store reviews in CSV file
    #writer = csv_writer(args.source, args.i)
    

    with GoogleMapsScraper(debug=args.debug) as scraper:
        with open(args.i, 'r') as urls_file:
            for url in urls_file:
                writer = csv_writer(args.source, f"{args.i}_{url[54:76]}")
                address = scraper.get_address(url)
                if args.place:
                    print(scraper.get_account(url))
                else:
                    error = scraper.sort_by(url, ind[args.sort_by])
                    print(error)

                if error == 0:

                    n = 0

                    if ind[args.sort_by] == 0:
                        scraper.more_reviews()
                    
                    
                    print(address)
                    while n < args.N:
                        print(colored('[Review ' + str(n) + ']', 'cyan'))
                        reviews = scraper.get_reviews(n)

                        for r in reviews:
                            row_data = list(r.values()) 
                            if args.source:
                                row_data.append(url[:-1])
                                row_data.append(address)

                            writer.writerow(row_data)

                        n += len(reviews)
