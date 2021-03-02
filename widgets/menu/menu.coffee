class Dashing.Menu extends Dashing.Widget
  ready: ->
  # This is fired when the widget is done being rendered

  onData: (data) ->
    # Fired when you receive data
    for key,value of data
      break if key in ["id","updatedAt"]
      id = $(@node).find("##{key}")
      console.log(id)
      [error,warning] = value.split("/")
      if error != "0"
        id.attr("class","value-error")
      else if warning != "0"
        id.attr("class","value-warning")
      else
        id.attr("class","value-ok")
