var timeplot;

function onLoad() {
  var eventSource = new Timeplot.DefaultEventSource();
  var eventSource2 = new Timeplot.DefaultEventSource();

  var timeGeometry = new Timeplot.DefaultTimeGeometry({
    gridColor: new Timeplot.Color("#000000"),
    axisLabelsPlacement: "top"
  });

  var valueGeometry = new Timeplot.DefaultValueGeometry({
    gridColor: "#000000",
    min: 0,
    max: 100
  });

  var plotInfo = [
    Timeplot.createPlotInfo({
      id: "activenodes",
      dataSource: new Timeplot.ColumnSource(eventSource, 1),
      timeGeometry: timeGeometry,
      valueGeometry: valueGeometry,
      lineColor: "#ff0000",
      fillColor: "#cc8080",
      showValues: true
    }),
    Timeplot.createPlotInfo({
      id: "brokennodes",
      dataSource: new Timeplot.ColumnSource(eventSource, 2),
      timeGeometry: timeGeometry,
      valueGeometry: valueGeometry,
      lineColor: "#D0A825",
      showValues: false
    }),
    Timeplot.createPlotInfo({
      id: "oldversionnodes",
      dataSource: new Timeplot.ColumnSource(eventSource, 3),
      timeGeometry: timeGeometry,
      valueGeometry: valueGeometry,
      lineColor: "#25A8a0",
      showValues: true
    }),
    Timeplot.createPlotInfo({
      id: "versions",
      timeGeometry: timeGeometry,
      valueGeometry: valueGeometry,
      eventSource: eventSource2,
      lineColor: "#03212E"
    })
  ];
  
  timeplot = Timeplot.create(document.getElementById("my-timeplot"), plotInfo);
  timeplot.loadText("node_overview.txt", ",", eventSource);
  timeplot.loadXML("version_events.xml", eventSource2);
}

var resizeTimerID = null;
function onResize() {
    if (resizeTimerID == null) {
        resizeTimerID = window.setTimeout(function() {
            resizeTimerID = null;
            timeplot.repaint();
        }, 100);
    }
}

