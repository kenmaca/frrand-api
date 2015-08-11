# OTW API
## Notes
Striked out items indicate soon-to-be-depreciated items and should be removed/changed ASAP.

## Login

### Login: GET http://otw.kenma.ca/login
#### Variables
* username: `a unique username`
* password: `password`
* gcmInstanceId: `instance id for GCM`

#### Returns
##### Success: 200
* ~~apiToken: `an assigned API key`~~
###### GCM
* apiKey: `an assigned API key`

##### Failure: 401
None

## Users

### Registers an Account: POST http://otw.kenma.ca/users
#### Variables
* username: `a unique username`
* password: `password`
* ~~homeAddress: `full street name`~~
* ~~homeCity: `city`~~
* ~~homeRegion: `region (province)`~~
* ~~homeCountry: `country`~~
* ~~homePostal: `postal/zip code`~~
* ~~homeUnit: `unit #`~~

#### Returns
##### Success: 201
None

##### Failure: 409
* msg: "User already exists"

### Gets all Users: GET http://otw.kenma.ca/users
#### Returns
##### Success: 200
* users: `[an user, ..]`

## Location
### Logs a Current Location: POST /users/`username`/location
#### Headers
* Authorization: `apiKey for username`

#### Variables
* longitude: `longitude`
* latitude: `latitude`

#### Returns
##### Success: 201
None

##### Failure: 403
* msg: "API Key is unauthorized to modify `username`"

### Gets all Reported Locations for an User: GET /users/`username`/location
#### Headers
* Authorization: `apiKey for username`

#### Returns
##### Success: 200
* lastReportedLocations: `[a reported location, ..]`

##### Failure: 403
* msg: "API Key is unauthorized to access `username`"

### Gets the Route an User travelled through a certain period: GET /users/`username`/location/routes/`start time`/`end time`
#### Headers
* Authorization: `apiKey for username`

#### Returns
##### Success: 200
* type: "LineString"
* coordinates: `[[longitude, latitude], ..]`

##### Failure: 400
* msg: "Start time is ahead of end time"

##### Failure: 403
* msg: "API Key is unauthorized to access `username`

### Gets a Grid of all Stationary Locations for an User: GET /users/`username`/location/grid
#### Headers
* Authorization: `apiKey for username`

#### Returns
##### Success: 200
* username: `username`
* dayOfWeek: `{day of week 1-7: {hour 0-23: {location id: [time object, ..], ..}, ..}, ..}`
* updated: `time object`

##### Failure: 403
* msg: "API Key is unauthorized to access `username`
