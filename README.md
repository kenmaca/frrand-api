# OTW API

## Login
### Login: GET http://otw.kenma.ca/login
#### Headers

* None

#### Variables

* username: {{ a unique username }}
* password: {{ password }}

#### Returns (via JSON)

* apiToken: {{ an assigned API key }}

## Users
### Register an Account: POST http://otw.kenma.ca/users
#### Headers

* username: {{ a unique username }}
* password: {{ password }}
* homeAddress: {{ full street name }}
* homeCity: {{ city }}
* homeRegion: {{ region (province) }}
* homeCountry: {{ country }}
* homePostal: {{ postal/zip code }}
* homeUnit: {{ unit # }}
