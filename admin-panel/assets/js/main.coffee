# Global Helpers
toast = (msg, duration = 2000, warn = 'toast-neutral') ->
  Materialize.toast msg, duration, warn
capitalize = (str) ->
  # return capitalized string from any type
  return _.capitalize String(str)
# Global Constants
# API_ENDPOINT = 'https://dev-api.frrand.com'
API_ENDPOINT = 'https://api.frrand.com'
HTTP_SETTINGS = {
    headers: {
      # Kenneth's API key :D 
      # Authorization: 'IBJKYFHFFZLCZHVDSYZFWABYAJWSJECM'
      # Prod Key (Alex)
      Authorization: 'JVJGBQEEOOGKVTSCHRXCIMJSZRGCNSAI'
      'Content-Type': 'application/json'
    }
  }

Home = Vue.extend {
  template: '#home-template'
  http: HTTP_SETTINGS
  data: -> {
    test: 'Hello World.'
    users: []
  }
  methods: {
    dummyMethod: ->
      return 'Hello world! ' + this.test
    getRequests: ->
      this.$http.get "#{API_ENDPOINT}/profiles", (data, status, req) ->
        if status == 200
          console.log data
      return
  }
  created: ->
    console.log 'Home is ready'
    $(".sidebar").css 'height', $(window).height()
  ready: ->
    console.log ''
    

}

Users = Vue.extend {
  template: '#users-template'
  http: HTTP_SETTINGS
  data: -> {
    test: 'Hello World.'
    users: []
    stats: {
      today: 0
    }
  }
  methods:
    patchUser: (user) ->
      _keys = ["username","active","points","rating","requestsDelivered","requestsRecieved","deviceType"]
      # Only patch the fields in the specified keys
      _data = _.pick(user, _keys)
      _data.active = _data.active == 'true' or _data.active == 'True'
      _data.rating = parseFloat _data.rating
      this.$http.patch "#{API_ENDPOINT}/adminUsers/" + user._id, _data, {'headers': {'If-Match': user._etag}}
        .then (resp) ->
          console.log resp
          toast "Succesfully patched [#{user.username}].", 2000, 'toast-positive'
          return true
        , (resp) ->
          console.log 'error', resp
          toast "Failed to patch [#{user.username}]!", 2000, 'toast-negative'
          return false
    calcUserStats: ->
      # Calculate user stats
      _today = moment().format('DDMMYYYY')
      for _user in this.users
        _date = moment(new Date(_user._created))
        if _date.format('DDMMYYYY') == _today
          this.stats.today += 1


    initUserTable: ->
      that = this
      $('#users-table').jsGrid({
      height: "auto"
      width: "100%"
      editing: true
      sorting: true
      autoload: true
      # filtering: true      
      # paging: true
      # pageLoading: true
      # pageSize: 30
      controller: {
        loadData: (filter) ->
          d = $.Deferred()
          that.$http.get "#{API_ENDPOINT}/adminUsers?max_results=500"
            .then (resp) ->
              check = false
              for k in filter
                if !filter[k]
                  check = true
              filterCheck = (obj) ->
                for k in filter
                  if (k in obj && obj[k] == filter[k])
                    return true
                return false
              result = resp.data._items
              if check
                console.log 'Checking against our filter'
                result = result.filter(filterCheck)
              d.resolve result
              console.log result
              that.users = result
            , (resp) ->
              console.log 'failed'
              return 0
          return d.promise()

      }
      # controller: $.parseJSON(JSON.stringify(this.users))
      fields: [
        {name: 'username', title: 'Username', type: "text", width: 100}
        {name: 'active', title: 'Active', type: 'text', width: 50, align: 'center', "itemTemplate": (val) -> capitalize(val) }
        {name: 'phone', title: 'Phone', type: "text", width: 110, align: 'center', editing: false}
        {name: 'points', title: 'Points', type: "number", width: 60, align: 'center'}
        {name: 'rating', title: 'Rating', type: "text", width: 60, align: 'center', itemTemplate: (val) ->
          return parseFloat(val).toFixed(2)}
        {name: 'requestsDelivered', title: 'Delivered', type: "number", width: 70, align: 'center'}
        {name: 'requestsRecieved', title: 'Recieved', type: "number", width: 70, align: 'center'}
        {name: 'deviceType', title: 'Platform', type: "text", width: 70, align: 'center'}
        {name: '_created', title: 'Created', type: "text", width: 150, align: 'center', editing: false, "itemTemplate": (val) ->
          return moment(new Date(val)).format('ddd, MMM DD @ hh:mm A')
        , sorter: (date1, date2) ->
            return new Date(date1) - new Date(date2) }
        {type: 'control', width: 50}
      ]
      # rowClick: (args) ->
      #   console.log args
      onItemUpdated: (args) ->
        # console.log args
        if that.patchUser args.item
          return true
        else
          return false
      onRefreshed: (args) ->
        _height = $("#users-table").height() + 20
        _winHeight = $(window).height()
        _height = if _height > _winHeight then _height else _winHeight
        $('.sidebar').height _height
      })
  created: ->
    console.log 'ready'
  ready: ->
    console.log "Hello world!"
    this.initUserTable()
    this.calcUserStats()
}

Requests = Vue.extend {
  template: '#requests-template'
  http: HTTP_SETTINGS
  data: -> {
    test: 'Hello World.'
    users: []
    requests: []
    addresses: []
    map: {}
    mapOverlap: {}
    mapObjects: []
    requestsCancelled: 0
    requestsCompleted: 0
    requestsPending: 0
  }
  methods: {
    getUsers: ->
      this.$http.get "#{API_ENDPOINT}/adminUsers?max_results=500"
        .then (resp) ->
          this.users = resp.data._items
          return true
        , (resp) ->
          console.log "Failed to grab Users."
          toast 'Failed to grab Users from DB.', 5000, 'toast-negative'
          return false
    getAddress: (addr) ->
      # get a single address from db with address ID
      this.$http.get "#{API_ENDPOINT}/adminAddresses/#{addr}"
        .then (resp) ->
          console.log resp
          return true
        , (resp) ->
          console.log resp
          return false
    getAddresses: ->
      # get all addresses from db and store locally
      this.$http.get "#{API_ENDPOINT}/adminAddresses"
        .then (resp) ->
          this.addresses = resp.data._items
          return true
        , (resp) ->
          console.log resp
          return false
    liveUpdateHandler: ->
      console.log 'Updating...'
      toast 'Fetching data from DB'
      # this.initMap()
      $('#requests-table').jsGrid 'loadData'
    initMap: ->
      # Initialize Google Maps Object
      toronto = new google.maps.LatLng(43.6532, -79.3832)
      this.map = new google.maps.Map document.getElementById("requests-map"), {
        zoom: 13
        # center: myLatLng
      }
      that = this
      handleNoGeolocation = (errorFlag) ->
        if errorFlag == true
          initialLocation = toronto
        else
          initialLocation = toronto
        that.map.setCenter initialLocation
        return

      if navigator.geolocation
        browserSupportFlag = true
        navigator.geolocation.getCurrentPosition ((position) ->
          initialLocation = new (google.maps.LatLng)(position.coords.latitude, position.coords.longitude)
          that.map.setCenter initialLocation
          return
        ), ->
          handleNoGeolocation browserSupportFlag
          return
      else
        browserSupportFlag = false
        handleNoGeolocation browserSupportFlag

      # init marker spiderfier
      this.mapOverlap = new OverlappingMarkerSpiderfier this.map
      iw = new google.maps.InfoWindow()
      # Clear path highlighting on clicking close in the InfoWindow
      google.maps.event.addListener iw, 'closeclick', ->
        console.log 'Closed marker!'
        this._path.setMap null

      this.mapOverlap.addListener 'click', (marker, event) ->
        # Path highlighting
        iw._path = new google.maps.Polyline {
          path: marker.routes
          geodesic: true
          strokeColor: '#00007f'
          strokeOpacity: 0.8
          strokeWeight: 3
        }
        # Makes sure the previous highlight path is closed
        if window._path
          window._path.setMap null
          window._path = iw._path
        else
          window._path = iw._path
        iw._path.setMap that.map
        # Init InfoWindow popup for each marker
        iw.setContent marker.desc
        iw.open that.map, marker
    initMapMarkers: (requests) ->
      # Initialize map markers on the map corresponding to existing requests
      that = this
      for req in requests
        # skip cancelled or completed requests
        if req.cancel or req.complete then continue
        _destinationAddr = _.find this.addresses, {_id: req.destination}
        console.log req.destination, this.addresses
        # If address does not exist, then try to check against a frefresh of our DB
        if not _destinationAddr
          this.getAddresses()
          _destinationAddr = _.find that.addresses, {_id: req.destination}
          if not _destinationAddr then continue
        _pickupAddr = req.places[0]
        user = this.findUser(req.createdBy)
        user = if user then user else {}
        _destinationXY = _destinationAddr.location.coordinates
        _pickupXY = _pickupAddr.location.coordinates

        # Build route polyline
        _routes = [{lat: _pickupXY[1], lng: _pickupXY[0]}, {lat: _destinationXY[1], lng: _destinationXY[0]}]
        _path = new google.maps.Polyline {
          path: _routes
          geodesic: true
          strokeColor: '#FF0000'
          strokeOpacity: 0.8
          strokeWeight: 1
        }

        # Build for pickup marker
        _pickupMarker = new google.maps.Marker {
          position: new google.maps.LatLng _pickupXY[1], _pickupXY[0]
          title: _pickupAddr.address
          map: this.map
          animation: google.maps.Animation.DROP
          routes: _routes
          icon: if location.hostname == "localhost" then '/assets/images/frrand-pickup-marker.png' else '/admin-panel/assets/images/frrand-pickup-marker.png' 
        }

        # build for destination marker
        LatLng = new google.maps.LatLng _destinationXY[1], _destinationXY[0]
        _destinationMarker = new google.maps.Marker {
          position: LatLng, title: _destinationAddr.address, routes: _routes,
          map: this.map, animation: google.maps.Animation.DROP,
          icon: if location.hostname == "localhost" then '/assets/images/frrand-marker.png' else '/admin-panel/assets/images/frrand-marker.png' 
        }
        _items = ""
        _cost = 0
        for _i, index in req.items
          _items += "<b>#{_i.quantity}</b>x - <b>#{_i.name}</b> for $#{_i.price.toFixed(2)}"
          _items += if index != req.items.length - 1 then '<br>' else '' 
          _cost += parseFloat(_i.price)

        _status = {}
        if req.cancel
          _status.class = 'marker-negative'
          _status.status = 'Cancelled'
        else if req.complete
          _status.class = 'marker-positive'
          _status.status = 'Completed'
        else if req.pickedUp
          _status.class = 'marker-positive'
          _status.status = 'Picked Up'
        else
          _status.class = 'marker-warning'
          _status.status = 'Pending - waiting for pickup'

        # Build the html for the marker info window
        _destinationMarker.desc = """
          <span><b class="center">#{user.username} [#{capitalize(_destinationAddr.name)}]</b></span><br>
          <span><em>#{user.phone} - [#{if user.rating then user.rating.toFixed(2) else 0}/5] - [#{user.points} pts] </em></span><br>
          <span><b>To:</b> #{_destinationAddr.address}</span><br>
          <span>#{if _destinationAddr.roomNumber then "<b>Room:</b> " + String(_destinationAddr.roomNumber) + " - " else ""} #{if _destinationAddr.buildingName then "<b>Building:</b> " + _destinationAddr.buildingName + "<br>" else ""} </span>
          <span><b>From:</b> #{_pickupAddr.address}</span><br>
          <hr><span>#{_items}</span><br>
          <hr>
          <span><b>Total: </b> $#{_cost.toFixed(2)}</span><br>
          <span><b>Delivery Time:</b> #{moment(new Date(req.requestedTime)).format('ddd, MMM MM @ hh:mm A')}</span><br>
          <span><b>Status:</b> <em class="#{_status.class}">#{_status.status}</em> </span>
        """

        _pickupMarker.desc = """
          <b>#{_pickupAddr.address}</b><br>
          <hr><span>#{_items}</span><br>
          <hr>
          <span><b>Total: </b> $#{_cost.toFixed(2)}</span><br>
          <span><b>Requester: </b> #{user.username}</span><br>
          <span><b>Delivery Time:</b> #{moment(new Date(req.requestedTime)).format('ddd, MMM MM @ hh:mm A')}</span><br>
        """



        _path.setMap this.map
        # History tracking of what we've drawn on the map
        _historyObj = {_id: req._id, to: _destinationMarker, _from: _pickupMarker, path: _path, req: req}
        this.mapObjects.push _historyObj

        this.mapOverlap.addMarker _destinationMarker
        this.mapOverlap.addMarker _pickupMarker
        console.log 'Plotting', _destinationAddr
        # marker.setMap this.map

    findUser: (id) ->
      # Find the user object with the given _id
      # Return user if found, null otherwise
      _user = _.find this.users, {'_id': id}
      that = this
      if not _user
        this.getUsers().then ->
          _user = _.find that.users, {'_id': id}
      return  _user or null
    calcStats: ->
      cancelled = _.filter this.requests, {'cancel': true}
      completed = _.filter this.requests, {'complete': true}
      pending = _.filter this.requests, {'cancel': false, 'complete': false}
      this.requestsCancelled = cancelled.length or 0
      this.requestsCompleted = completed.length or 0
      this.requestsPending = pending.length or 0
    getRequests: ->
      this.$http.get "#{API_ENDPOINT}/adminRequests"
        .then (resp) ->
          this.requests = resp.data._items
          return true
        , (resp) ->
          console.log resp
          return false
    initRequestsTable: ->
      that = this
      $('#requests-table').jsGrid({
        height: "auto"
        width: "100%"
        # editing: true
        sorting: true
        autoload: true
        controller: {
          loadData: (filter) ->
            d = $.Deferred()
            that.$http.get "#{API_ENDPOINT}/adminRequests"
              .then (resp) ->
                result = resp.data._items
                d.resolve result
                that.requests = result
                # console.log result
                # Calculate request stats
                that.calcStats()
                # On live update
                if that.mapObjects.length != 0
                  # After initial load
                  removeFromMap = (obj) ->
                    # remove from map, using history obj
                    that.mapOverlap.removeMarker obj.to
                    that.mapOverlap.removeMarker obj._from
                    obj.to.setMap null
                    obj._from.setMap null
                    obj.path.setMap null

                  # Get list of requests that are plottable
                  _pending = _.filter that.requests, {'cancel': false, 'complete': false}
                  _toAdd = []
                  for _pendingObj in _pending
                    _find = _.find that.mapObjects, {_id: _pendingObj._id}
                    if _find
                      if _.isEqual _find.req, _pendingObj
                        continue
                      else
                        # Something changed, remove, readd if its not cancelled/complete
                        if _pendingObj.cancel or _pendingObj.complete
                          removeFromMap _find
                        else
                          removeFromMap _find
                          _toAdd.push _pendingObj
                        _.remove that.mapObjects, {_id: _pendingObj._id}
                    else
                      # Doesn't exist on the map, add it
                      _toAdd.push _pendingObj
                  that.initMapMarkers _toAdd
                else
                  # New load
                  that.initMapMarkers(that.requests)
                return true
              , (resp) ->
                console.log 'failed'
                return false
            return d.promise()

        }
        # controller: $.parseJSON(JSON.stringify(this.users))
        fields: [
          {name: 'createdBy', title: 'Username', type: "text", width: 100, editing: false, itemTemplate: (val) ->
            _x = that.findUser(val)
            return if _x then _x.username else 'Unknown'}
          {name: 'cancel', title: 'Cancelled', type: "text", align: 'center', width: 80, "itemTemplate": (val) -> capitalize(val) }
          {name: 'complete', title: 'Complete', type: "text", align: 'center', width: 80, "itemTemplate": (val) -> capitalize(val) }
          {name: 'attachedInviteId', title: 'Attached', type: "text", align: 'center', width: 80, "itemTemplate": (val) -> 
            if val then return 'Yes' else return 'No'  }
          # {name: 'points', title: 'Points', type: "number", align: 'center', width: 60}
          {name: 'items', title: 'Items', type: "string", align: 'center', width: 80, itemTemplate: (val) ->
            out = ""
            for o, index in val
              out += "<b>#{o.quantity}</b>x - #{o.name}</br>"
            return out }
          {name: 'items', title: 'Cost', type: "string", align: 'center', width: 80, itemTemplate: (val) ->
            out = 0
            for o in val
              out += parseInt o.price
            return "$#{out.toFixed(2)}"
          , sorter: (v1, v2) ->
            t = (o) ->
              _out = 0
              for i in o
                _out += parseInt i.price
              return _out 
            return t(v1) - t(v2) }
          {name: '_created', title: 'Created', type: "text", width: 150, align: 'center', editing: false, "itemTemplate": (val) ->
              return moment(new Date(val)).format('ddd, MMM DD @ hh:mm A')
          , sorter: (date1, date2) ->
              return new Date(date1) - new Date(date2) }
          {name: 'requestedTime', title: 'Pickup', type: "text", width: 80, align: 'center', editing: false, "itemTemplate": (val) ->
              return moment(new Date(val)).format('hh:mm A')
          , sorter: (date1, date2) ->
              return new Date(date1) - new Date(date2) }
          {name: 'places', title: 'From:', type: "text", width: 150, align: 'center', itemTemplate: (val) ->
            return val[0].address
          }
          # {type: 'control', width: 50}
        ]
        onRefreshed: (args) ->
          _height = $("#requests-table").height() + 600
          _winHeight = $(window).height()
          _height = if _height > _winHeight then _height else _winHeight
          $('.sidebar').height _height
        rowClick: (args) ->
          # that.getAddress args.item.destination
          # that.getAddresses()
      })

    testFn: ->
      this.getRequests()
  }
  ready: ->
    that = this
    console.log '[Requests Page] - Ready'

    $(->
      that.getUsers().then ->
        that.getAddresses().then ->
          that.initMap()
          that.initRequestsTable()
          window.liveUpdateTimer = setInterval that.liveUpdateHandler, 30000
    )
  beforeDestroy: ->
    window.clearInterval window.liveUpdateTimer
}

router = new VueRouter()

router.map {
  '/': {
    component: Home
  }
  '/users': {
    component: Users
  }
  '/requests': {
    component: Requests
  }
}

App = Vue.extend {}
router.start App, '#app'

