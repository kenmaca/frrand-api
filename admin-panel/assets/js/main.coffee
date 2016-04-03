# Global Helpers
toast = (msg, duration = 2000, warn = 'toast-neutral') ->
  Materialize.toast msg, duration, warn

Home = Vue.extend {
  template: '#home-template'
  http: {
    headers: {
      # Kenneth's API key :D 
      Authorization: 'IBJKYFHFFZLCZHVDSYZFWABYAJWSJECM'
    }
  }
  data: {
    test: 'Hello World.'
    users: []
  }
  methods: {
    dummyMethod: ->
      return 'Hello world! ' + this.test
    getRequests: ->
      this.$http.get 'https://dev-api.frrand.com/profiles', (data, status, req) ->
        if status == 200
          console.log data
      return
  }
  created: ->
    console.log 'Home is ready'
  ready: ->
    console.log "Hello world!"

}

Users = Vue.extend {
  template: '#users-template'
  http: {
    headers: {
      # Kenneth's API key :D 
      Authorization: 'IBJKYFHFFZLCZHVDSYZFWABYAJWSJECM'
      'Content-Type': 'application/json'
    }
  }
  data: {
    test: 'Hello World.'
    users: []
  }
  methods:
    patchUser: (user) ->
      _keys = ["username","active","phone","points","rating","requestsDelivered","requestsRecieved","deviceType"]
      # Only patch the fields specified keys
      _data = _.pick(user, _keys)
      _data.active = _data.active == 'true'
      this.$http.patch 'https://dev-api.frrand.com/adminUsers/' + user._id, _data, {'headers': {'If-Match': user._etag}}
        .then (resp) ->
          console.log resp
          toast "Succesfully patched [#{user.username}].", 2000, 'toast-positive'
          return true
        , (resp) ->
          console.log 'error', resp
          toast "Failed to patch [#{user.username}]!", 2000, 'toast-negative'
          return false
    # loadUsers: ->
    #   this.$http.get 'https://dev-api.frrand.com/adminUsers'
    #     .then (resp) ->
    #       console.log 'success', resp.data
    #       this.initUserTable()
    #       return resp.data
    #     , (resp) ->
    #       console.log 'failed'
    #       return 0
    #   return

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
          that.$http.get 'https://dev-api.frrand.com/adminUsers'
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
        {name: 'username', title: 'Username', type: "text", width: 50}
        {name: 'active', title: 'Active', type: 'text', width: 20, align: 'center', "itemTemplate": (val) ->
            return _.capitalize String(val) }
        {name: 'phone', title: 'Phone', type: "text", width: 45, align: 'center'}
        {name: 'points', title: 'Points', type: "number", width: 20, align: 'center'}
        {name: 'rating', title: 'Rating', type: "number", width: 10, align: 'center'}
        {name: 'requestsDelivered', title: 'Delivered', type: "number", width: 20, align: 'center'}
        {name: 'requestsRecieved', title: 'Recieved', type: "number", width: 20, align: 'center'}
        {name: 'deviceType', title: 'Platform', type: "text", width: 35, align: 'center'}
        {name: '_created', title: 'Created', type: "text", width: 50, align: 'center', editing: false, "itemTemplate": (val) ->
            return val.slice(0,-4)
        }
        {type: 'control', width: 10}
      ]
      # rowClick: (args) ->
      #   console.log args
      onItemUpdated: (args) ->
        # console.log args
        return that.patchUser args.item
      })
  created: ->
    console.log 'ready'
  ready: ->
    console.log "Hello world!"
    this.initUserTable()
}

router = new VueRouter()

router.map {
  '/': {
    component: Home
  }
  '/users': {
    component: Users
  }
}

App = Vue.extend {}
router.start App, '#app'

