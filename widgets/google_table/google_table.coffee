class Dashing.GoogleTable extends Dashing.Widget

  @accessor 'current', ->
    return @get('displayedValue') if @get('displayedValue')
    points = @get('points')
    #if points
    #  points[points.length - 1].y

  ready: ->
    container = $(@node).parent()
  # Gross hacks. Let's fix this.
  #  width = (Dashing.widget_base_dimensions[0] * container.data("sizex")) + Dashing.widget_margins[0] * 2 * (container.data("sizex") - 1)
  #  height = (Dashing.widget_base_dimensions[1] * container.data("sizey")) + Dashing.widget_margins[1] * 2 * (container.data("sizey") -1)

    @chart = new google.visualization.Table($(@node).find(".chart")[0])
    @options =
      height: height
      width: width
      colors: colors
      backgroundColor:
        fill:'transparent'


    if @get('points')
      @data = google.visualization.arrayToDataTable @get('points')
    else
      @data = google.visualization.arrayToDataTable []

    @chart.draw @data, @options

  onData: (data) ->
    if @chart
      @data = google.visualization.arrayToDataTable data.points
      @chart.draw @data, @options
