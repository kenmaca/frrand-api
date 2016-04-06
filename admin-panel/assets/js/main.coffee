# Global Helpers
toast = (msg, duration = 2000, warn = 'toast-neutral') ->
  Materialize.toast msg, duration, warn
capitalize = (str) ->
  # return capitalized string from any type
  return _.capitalize String(str)
# Global Constants
API_ENDPOINT = 'https://dev-api.frrand.com'
HTTP_SETTINGS = {
    headers: {
      # Kenneth's API key :D 
      Authorization: 'IBJKYFHFFZLCZHVDSYZFWABYAJWSJECM'
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
          that.$http.get "#{API_ENDPOINT}/adminUsers"
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
        {name: 'rating', title: 'Rating', type: "text", width: 60, align: 'center'}
        {name: 'requestsDelivered', title: 'Delivered', type: "number", width: 70, align: 'center'}
        {name: 'requestsRecieved', title: 'Recieved', type: "number", width: 70, align: 'center'}
        {name: 'deviceType', title: 'Platform', type: "text", width: 70, align: 'center'}
        {name: '_created', title: 'Created', type: "text", width: 150, align: 'center', editing: false, "itemTemplate": (val) ->
            return val.slice(0,-4)
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
        _height = $("#users-table").height()
        _winHeight = $(window).height()
        _height = if _height > _winHeight then _height else _winHeight
        $('.sidebar').height _height
      })
  created: ->
    console.log 'ready'
  ready: ->
    console.log "Hello world!"
    this.initUserTable()
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
  }
  methods: {
    getUsers: ->
      this.$http.get "#{API_ENDPOINT}/adminUsers"
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
    initMapMarkers: ->
      # Initialize map markers on the map corresponding to existing requests
      for req in this.requests
        if req.cancel or req.complete then continue
        _destinationAddr = _.find this.addresses, {_id: req.destination}
        _pickupAddr = req.places[0]
        user = this.findUser(req.createdBy)
        _destinationXY = _destinationAddr.location.coordinates
        LatLng = new google.maps.LatLng _destinationXY[1], _destinationXY[0]
        _destinationMarker = new google.maps.Marker {
          position: LatLng, title: _destinationAddr.address
          , map: this.map, animation: google.maps.Animation.DROP,
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
          <span><em>#{user.phone} - [#{user.rating}/5] - [#{user.points} pts] </em></span><br>
          <span><b>To:</b> #{_destinationAddr.address}</span><br>
          <span><b>From:</b> #{_pickupAddr.address}</span><br>
          <span>#{if _destinationAddr.roomNumber then "<b>Room:</b> " + _destinationAddr.roomNumber +" - " else ""} #{if _destinationAddr.buildingName then "<b>Building:</b> " + _destinationAddr.buildingName + "<br>" else ""} </span>
          <hr><span>#{_items}</span><br>
          <hr>
          <span><b>Total: </b> $#{_cost.toFixed(2)}</span><br>
          <span><b>Delivery Time:</b> #{moment(new Date(req.requestedTime)).format('ddd, MMM MM @ hh:mm A')}</span><br>
          <span><b>Status:</b> <em class="#{_status.class}">#{_status.status}</em> </span>
        """

        # Build for pickup marker
        _pickupXY = _pickupAddr.location.coordinates
        _pickupMarker = new google.maps.Marker {
          position: new google.maps.LatLng _pickupXY[1], _pickupXY[0]
          title: _pickupAddr.address
          map: this.map
          animation: google.maps.Animation.DROP
          icon: if location.hostname == "localhost" then '/assets/images/frrand-pickup-marker.png' else '/admin-panel/assets/images/frrand-pickup-marker.png' 
        }
        _pickupMarker.desc = """
          <b>#{_pickupAddr.address}</b>
        """

        # Build route polyline
        _routes = [{lat: _pickupXY[1], lng: _pickupXY[0]}, {lat: _destinationXY[1], lng: _destinationXY[0]}]
        _path = new google.maps.Polyline {
          path: _routes
          geodesic: true
          strokeColor: '#FF0000'
          strokeOpacity: 0.8
          strokeWeight: 1
        }
        _path.setMap this.map

        this.mapOverlap.addMarker _destinationMarker
        this.mapOverlap.addMarker _pickupMarker
        # marker.setMap this.map

    findUser: (id) ->
      # Find the user object with the given _id
      # Return user if found, null otherwise
      return _.find this.users, {'_id': id} or null
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
                console.log result
                that.requests = result
              , (resp) ->
                console.log 'failed'
                return false
            return d.promise()

        }
        # controller: $.parseJSON(JSON.stringify(this.users))
        fields: [
          {name: 'createdBy', title: 'Username', type: "text", width: 100, editing: false, itemTemplate: (val) ->
            return that.findUser(val).username}
          {name: 'cancel', title: 'Cancelled', type: "text", align: 'center', width: 80, "itemTemplate": (val) -> capitalize(val) }
          {name: 'complete', title: 'Complete', type: "text", align: 'center', width: 80, "itemTemplate": (val) -> capitalize(val) }
          {name: 'attachedInviteId', title: 'Attached', type: "text", align: 'center', width: 80, "itemTemplate": (val) -> 
            if val then return 'Yes' else return 'No'  }
          {name: 'points', title: 'Points', type: "number", align: 'center', width: 60}
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
              return val.slice(0,-4)
          , sorter: (date1, date2) ->
              return new Date(date1) - new Date(date2) }
          {name: 'requestedTime', title: 'Pickup Time', type: "text", width: 150, align: 'center', editing: false, "itemTemplate": (val) ->
              return val.slice(0,-4)
          , sorter: (date1, date2) ->
              return new Date(date1) - new Date(date2) }
          # {type: 'control', width: 50}
        ]
        onRefreshed: (args) ->
          _height = $("#requests-table").height() + 600
          _winHeight = $(window).height()
          _height = if _height > _winHeight then _height else _winHeight
          $('.sidebar').height _height
        rowClick: (args) ->
          # that.getAddress args.item.destination
          that.getAddresses()
      })

    testFn: ->
      this.getRequests()
  }
  ready: ->
    that = this
    console.log '[Requests Page] - Ready'
    # Load Google Maps
    initMap = ->

      toronto = new google.maps.LatLng(43.6532, -79.3832)
      that.map = new google.maps.Map document.getElementById("requests-map"), {
        zoom: 10
        # center: myLatLng
      }
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
      that.mapOverlap = new OverlappingMarkerSpiderfier that.map
      iw = new google.maps.InfoWindow()
      that.mapOverlap.addListener 'click', (marker, event) ->
        iw.setContent marker.desc
        iw.open that.map, marker

    $(->
      initMap()
      that.getUsers().then ->
        that.initRequestsTable()
      that.getAddresses().then ->
        that.getRequests().then ->
          that.initMapMarkers()
    )
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

