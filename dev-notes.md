
### [Git scraping:](https://simonwillison.net/2020/Oct/9/git-scraping/) track changes over time by scraping to a Git repository

[Simon Willison on gitscraping](https://simonwillison.net/tags/gitscraping/)  [git-scraping](https://github.com/topics/git-scraping) (Github Topics) [track changes over time by scraping to a Git repository | Hacker News](https://news.ycombinator.com/item?id=24732943)  [Raspando dados com o GitHub Actions e analisando com Datasette](https://docs.google.com/document/d/1TCatZP5gQNfFjZJ5M77wMlf9u_05Z3BZnjp6t1SA6UU/edit#heading=h.szw443oy1qgd)  

#### Examples

- [simonw/scrape-open-data](https://github.com/simonw/scrape-open-data) 
- [simonw/ca-fires-history](https://github.com/simonw/ca-fires-history)
- [simonw/cdc-vaccination-history](https://github.com/simonw/cdc-vaccination-history)
- [simonw/disaster-scrapers](https://github.com/simonw/disaster-scrapers/) 
- [simonw/scrape-roads-dot-ca-gov](https://github.com/simonw/scrape-roads-dot-ca-gov) 


### git-history

reads through the entire history of a file and generates a SQLite database reflecting changes to that file over time. [git-history:](https://simonwillison.net/2021/Dec/7/git-history/) a tool for analyzing scraped data collected using Git and SQLite [git-history - a tool for Datasette](https://datasette.io/tools/git-history)      

* * *

    [datadesk/california-coronavirus-scrapers](https://github.com/datadesk/california-coronavirus-scrapers) The open-source web scrapers that feed the Los Angeles Times California coronavirus tracker.     

* * *

   

### [GitHub Next | Flat Data](https://githubnext.com/projects/flat-data) 

[githubocto/flat-demo-bitcoin-price: A Flat Data GitHub Action demo repo](https://github.com/githubocto/flat-demo-bitcoin-price)  [pierrotsmnrd/flat\_data\_py_example: How to use Python in Github's Flat Data](https://github.com/pierrotsmnrd/flat_data_py_example)  [https://github.com/githubocto?q=flat-demo](https://github.com/githubocto?q=flat-demo)   
   

* * *

 

### [Automated Data Scraping with Github Actions](https://www.swyx.io/github-scraping) 

[swyxio/gh-action-data-scraping](https://github.com/swyxio/gh-action-data-scraping)

Instanțe
--------

- cmteb see also: [web.archive.org/ .. harta\_stare\_sistem\_termoficare\_bucuresti.php](https://web.archive.org/web/20221115000000*/https://www.cmteb.ro/harta_stare_sistem_termoficare_bucuresti.php) 
- situatie-drumuri
- [http://posturi.gov.ro/](http://posturi.gov.ro/) 
- [https://data.gov.ro/dataset](https://data.gov.ro/dataset) watch news?
- [https://data.gov.ro/dataset/mecanismul-de-feed-back-al-pacientului-2023](https://data.gov.ro/dataset/mecanismul-de-feed-back-al-pacientului-2023)  read latest json - check weekly
- CKAN analysis see [fetch data.gov.ro.docx](https://docs.google.com/document/d/1Emrco1IWSVUrHCGGPlFBf8qqCEucECJi/)'
- [https://extranet.brasovcity.ro/MapServer2/WebGis2/wgd/getmap.aspx](https://extranet.brasovcity.ro/MapServer2/WebGis2/wgd/getmap.aspx?_=1693784703515)  [https://extranet.brasovcity.ro/MapServer2/WebGis2/wgd/](https://extranet.brasovcity.ro/MapServer2/WebGis2/wgd/)

  
Structured data.gov.ro monthly dumps versioned as: [https://data.gov.ro/dataset/activity/mecanismul-de-feed-back-al-pacientului-2023](https://data.gov.ro/dataset/activity/mecanismul-de-feed-back-al-pacientului-2023)  check docs w multiple versions  

Roadmap
-------

Prometeu

- [x] read target into local (to repository) json
    - [x] cmteb
    - [x] andnet
- [ ] add meaningful commit msgs
- [x] save as csv
- [ ] check if changed before saving
- [ ] write to external repo
- [ ] build to datasette, FlatGithub
- [ ] get historical data