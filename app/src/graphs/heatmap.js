import React, { Component } from 'react'

import * as d3 from "d3";
import { select } from 'd3-selection'

export default class Heatmap extends Component {
  constructor(props) {
    super(props);

    this.margin = {top: 30, right: 30, bottom: 30, left: 30};
    this.width  = this.props.width - this.margin.left - this.margin.right;

    this.resetGraph();
    this.createVisualization(this.props.network);
    this.height = this.proposals.length * (this.props.width/this.participants.length);
  }

  resetGraph() {
    select(this.node).selectAll("*").remove();
    this.proposals = [];
    this.participants = [];
    this.affinities = [];
  }

  componentDidMount() {
    this.resetGraph();
    this.createVisualization(this.props.network)
    this.height = this.proposals.length * (this.props.width/this.participants.length);
  }

  componentDidUpdate() {
    this.resetGraph();
    this.createVisualization(this.props.network)
    this.height = this.proposals.length * (this.props.width/this.participants.length);
  }

  initialize() {
    let self = this;

    this.graph = select(self.node)
      .append("g")
      .attr("transform",
          "translate(" + self.margin.left + "," + self.margin.top + ")");

    // Build X scales and axis:
    this.x = d3.scaleBand()
      .range([ 0, self.width ])
      .domain(self.participants)
      .padding(0.01);
    this.graph.append("g")
      .attr("transform", "translate(0," + self.height + ")")
      .call(d3.axisBottom(self.x))

    this.y = d3.scaleBand()
      .range([self.height, 0 ])
      .domain(self.proposals)
      .padding(0.01);
    this.graph.append("g")
      .call(d3.axisLeft(self.y));

    // Build color scale
    this.myColor = d3.scaleLinear()
      .range(["white", "#69b3a2"])
      .domain([0,1])

    this.graph.selectAll()
      .data(self.affinities, function(d) {return d.source.id+':'+d.target.id})
      .enter()
      .append("rect")
      .attr("x", function(d) { return self.x(d.source.id)})
      .attr("y", function(d) { return self.y(d.target.id)})
      .attr("width", self.x.bandwidth() )
      .attr("height",self.y.bandwidth() )
      .style("fill", function(d) { return self.myColor(d.affinity)} )
  }

  createVisualization(network) {
    this.appendNodes(network.nodes)
    this.appendLinks(network.links);

    this.initialize()
  }

  appendLinks(links) {
    for (let l=0; l<links.length;l++) {
      if (links[l].type === "support") {
        this.affinities.push(links[l]);
      }
    }
  }

  appendNodes(nodes) {
    for (let n=0; n<nodes.length;n++) {
      if (nodes[n].type === "participant") {
        this.participants.push(nodes[n].id);
      } else if (nodes[n].type === "proposal") {
        this.proposals.push(nodes[n].id);
      }
    }
  }

  render() {
    return (
      <div ref={this.graphRef}>
        <svg
          id="heatmap"
          ref={node => (this.node = node)}
          width={this.props.width + this.margin.right}
          height={this.height + this.margin.bottom + this.margin.top }
        />
      </div>
    )
  }
}
