import React, { Component } from 'react';

import * as d3 from "d3";
import { select } from 'd3-selection'

var vesting_graph = false;

export default class VestingGraph extends Component {
  constructor(props) {
    super(props);
    this.width = this.props.width;
    this.height = this.props.height;
    this.margin = {
      top: 30,
      right: 50,
      bottom: 60,
      left: 30,
    }
    this.xaxis_mode = "Weeks";
    this.graphRef = React.createRef();

    this.initialize = this.initialize.bind(this);

    vesting_graph = this;
  }

  componentDidMount() {
    this.initialize();
  }

  componentDidUpdate() {
    this.svg.selectAll("*").remove();
    this.initialize();
  }

  initialize() {
    this.svg = select(this.node);
    let xaxis_ticks = this.props.weeks;
    let cliff = this.props.cliff;
    this.datapoints = this.props.weeks + 1;
    
    let cliff_values_vested = [];
    for (let i=0; i<cliff;i++) {
      cliff_values_vested.push({"y": 0});
    }

    let cliff_values_locked = [];
    for (let i=0; i<cliff;i++) {
      cliff_values_locked.push({"y": 1});
    }

    this.dataset_locked = d3.range(0, this.datapoints)
      .map(function(d) { 
        return {"y": Math.pow(1/2, d)} ;
      });

    this.dataset_vested = d3.range(0, this.datapoints)
      .map(function(d) { 
        return {"y": 1 - Math.pow(1/2, d)} ;
      });

    this.dataset_locked = [...cliff_values_locked, ...this.dataset_locked];
    this.dataset_vested = [...cliff_values_vested, ...this.dataset_vested];
    if (this.props.weeks < 29) {
      //this.xaxis_mode = "Weeks";
    } else if (this.props.weeks < 105) {
      //this.xaxis_mode = "Months";
      xaxis_ticks = this.props.weeks / 4;
    } else {
      //this.xaxis_mode = "Years";
      xaxis_ticks = this.props.weeks / 52;
    }

    this.x = d3.scaleLinear()
    .domain([0, vesting_graph.props.weeks])
    .range([vesting_graph.margin.left, vesting_graph.props.width - vesting_graph.margin.right]);

    this.y = d3.scaleLinear()
      .domain([0, 1])
      .range([vesting_graph.height - vesting_graph.margin.bottom, vesting_graph.margin.top]);

    this.xAxis = (g) => g
      .attr("transform", `translate(30,${this.height - this.margin.bottom})`)
      .call(d3.axisBottom(this.x).ticks(xaxis_ticks).tickSizeOuter(0));

    this.svg.append("text")
      .attr("transform",
            "translate(" + (this.width/2) + " ," +
                           (this.height - 10 ) + ")")
      .style("text-anchor", "middle")
      .style("stroke", "whitesmoke")
      .text(this.xaxis_mode);

    this.yAxis = (g) => g
      .attr("transform", "translate(" + (30 + this.margin.left) + ",0)")
      .call(d3.axisLeft(vesting_graph.y))
      .call(g => g.select(".domain").remove())

    // text label for the y axis
    this.svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -1)
      .attr("x",0 - (this.height / 2))
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .style("stroke", "whitesmoke")
      .text("Percent vested");

    this.line = d3.line()
      .x(function(d, i) {  return vesting_graph.x(i);  }) // set the x values for the line generator
      .y(function(d) { return vesting_graph.y(d.y); }) // set the y values for the line generator
      .curve(d3.curveMonotoneX); // apply smoothing to the line

    this.locked_path = this.svg.append("path")
      .datum(vesting_graph.dataset_locked)
      .attr("fill", "none")
      .attr("stroke", "orange")
      .attr("stroke-width", 3)
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round")
      .attr("transform", `translate(30,0)`)
      .attr("d",vesting_graph.line);

    this.vested_path = this.svg.append("path")
      .datum(vesting_graph.dataset_vested)
      .attr("fill", "none")
      .attr("stroke", "steelblue")
      .attr("stroke-width", 3)
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round")
      .attr("transform", `translate(30,0)`)
      .attr("d",vesting_graph.line);

    this.svg.call(vesting_graph.hover, 
      vesting_graph.locked_path, vesting_graph.dataset_locked, 
      vesting_graph.vested_path, vesting_graph.dataset_vested);

    this.svg.append("g")
      .call(this.xAxis);

    this.svg.append("g")
      .call(this.yAxis);

    this.initialized = true;
  }

  hover(svg, locked_path, locked_dataset, vested_path, vested_dataset) {
    if ("ontouchstart" in document) svg
        .style("-webkit-tap-highlight-color", "transparent")
        .on("touchmove", moved)
        .on("touchstart", entered)
        .on("touchend", left)
    else svg
        .on("mousemove", moved)
        .on("mouseenter", entered)
        .on("mouseleave", left);

    const dot_locked = svg.append("g")
        .attr("display", "none");

    dot_locked.append("circle")
        .attr("r", 5)
        .style("stroke", "whitesmoke")
        .style("fill", "whitesmoke");

    dot_locked.append("text")
        .style("font", "12px sans-serif")
        .style("fill", "whitesmoke")
        .attr("text-anchor", "middle")
        .attr("y", -16);

    const dot_vested = dot_locked.clone(true);

    function moved() {
      d3.event.preventDefault();
      const xm = vesting_graph.x.invert(d3.event.offsetX);
      //const ym = vesting_graph.y.invert(d3.event.offsetY);
      const i1 = d3.bisectLeft([...locked_dataset.keys()], xm, 1);
      const i0 = i1 - 1;
      let i = xm - i0 > i1 -  xm ? i1 : i0;
      if (i === locked_dataset.length) {
        i = i -1;
      }
      const val_locked = locked_dataset[i].y;
      const val_vested = vested_dataset[i].y;
      locked_path.filter(d => d === val_locked).raise();
      vested_path.filter(d => d === val_vested).raise();
      dot_locked.attr("transform", `translate(${vesting_graph.x(i) + 30},${vesting_graph.y(val_locked)})`);
      dot_vested.attr("transform", `translate(${vesting_graph.x(i) + 30},${vesting_graph.y(val_vested)})`);
      let week_txt = " weeks";
      let vesting_txt_y_offset = 0 ;
      let txt_x_offset = 0 ;
      if (i === 0) {
        txt_x_offset = 40;
      }
      if ((d3.event.offsetX + 200) > vesting_graph.width) {
        txt_x_offset = vesting_graph.width - (d3.event.offsetX + 200);
      }

      if (i === 1) {
        week_txt = " week";
      }
      if (val_locked === val_vested) {
        vesting_txt_y_offset = -40;
      }

      dot_locked.select("text").text((val_locked * 100) + "% of tokens locked after " + i + week_txt).attr("transform",`translate(${txt_x_offset},0)` );
      dot_vested.select("text").text((val_vested * 100) + "% of tokens vested after " + i + week_txt).attr("transform",`translate(${txt_x_offset},${vesting_txt_y_offset})`);

    }

    function entered() {
      dot_vested.attr("display", null);
      dot_locked.attr("display", null);
    }

    function left() {
      dot_vested.attr("display", "none");
      dot_locked.attr("display", "none");
    }
  };

  render() {
      return (
        <div ref={this.graphRef}>
          <svg id="vesting" ref={node => this.node = node}
            width={this.props.width} height={this.props.height}>
          </svg>
        </div>
      )
   }
}
