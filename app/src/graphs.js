import * as d3 from "d3";
import React, { Component } from 'react';
import { filter } from './handlers';
import { select } from 'd3-selection'

export var simulation

const scrollToRef = (ref) => window.scrollTo(0, ref.current.offsetTop)

export default class ForceGraph extends Component {
  constructor(props) {
    super(props);
    this.width = this.props.width;
    this.height = this.props.width;
    this.graphRef = React.createRef();

    this.graphNodes = [];
    this.graphLinks = [];

    this.nodesById = {};
    this.linksById = {};

    this.color = d3.scaleOrdinal(d3.schemeAccent);

    this.getParticipantRadius = d3.scaleLinear()
           .domain([0,500000])
           .range([12,50]);

    this.getProposalRadius = d3.scaleLinear()
         .domain([0,50000])
         .range([6,20]);

    this.createVisualization = this.createVisualization.bind(this);
    this.nodeClick = this.nodeClick.bind(this);

  }

  scrollToGraph = () => {
    scrollToRef(this.graphRef);
  }

  componentDidMount() {
    this.createVisualization(this.props.network);
    this.scrollToGraph();
   }
   componentDidUpdate() {
    this.createVisualization(this.props.network);
   }
  // event callbacks
  dragstarted(simulation,d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
  }

  dragended(simulation,d) {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  } 
  // end event callbacks

  initialize() {
    var self = this;

    this.setupNodes();
    this.setupLinks();

    simulation = this.simulation = d3.forceSimulation(self.graphNodes)
        .force("link", d3.forceLink(self.graphLinks).id(function(d) { return d.id; }).distance(function (d) {return self.linkDistance(d)}))
        .force("charge_force", d3.forceManyBody(-20))
        .force("center_force", d3.forceCenter(self.width / 2, self.height / 2))
        .alphaDecay(0)
        .alphaMin(0)     
        .on("tick", function(){ self.tickActions(self.nodeCollection, self.linkCollection) });

    this.initialized = true;
  }

  setupNodes() {
    let self = this;
    this.nodeCollection = select(this.node).append("g")
        .attr("class", "nodes")
        .selectAll("circle")
        .data(this.graphNodes)
        .enter()
        .append("circle")
        .attr("r", function(d) {return self.getRadius(self, d)})
        .attr("fill", function(d) {return self.getColor(d)})
        .attr("stroke", "#fff").attr("stroke-width", 1.5)
        .call(d3.drag()
              .on("start", function(d){ self.dragstarted(self.simulation, d); } )
              .on("drag", function(d){ self.dragged(d); } )
              .on("end", function(d){ self.dragended(self.simulation, d); } ))  
        .on("click", function(d) {
          self.nodeClick(d);
          })
          
  }

  getColor(d) {
    if (d.type === 'participant') {
      return "#4090d9"; 
    }
    else if (d.type === 'proposal') {
      return "#53c388"; 
    }
    else {
      console.log("getColor: unknown node type");
    }
  }

  getRadius(simulation, d) {
    if (d.type === 'participant') {
      return Math.round(simulation.getParticipantRadius(d.holdings)); 
       }
    else if (d.type === 'proposal') {
      return Math.round(simulation.getProposalRadius(d.funds_requested));
    }
    else {
      console.log("getRadius: unknown node type");
    }
  }

  linkDistance(d) {
    return 200;
  }

  setupLinks(){
    this.linkCollection = select(this.node).append("g")
        .attr("class", "links")
        .selectAll(".link")
        .data(this.graphLinks)
        .enter()
        .append("line")
        .attr("stroke", "#808080")
        .attr("stroke-width", 1.0)
        .attr("pointer-events", "none")
        .attr("opacity", 0.0)
  }

  tickActions(node, link) {
    //update circle positions to reflect node updates on each tick of the simulation
    link
        .attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });
    node
        .attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });
  }
    
  nodeClick(selectedNode) {
    // reset all to unselected style

    d3.selectAll("line")
    .style("stroke","#808080")
    .style("stroke-width", 1.0)
    .style("opacity", 0.0)
    // select
    if (selectedNode.type === "participant") {
      d3.selectAll("line").filter(function(d) {
          return (d.type === filter && d.source.id === selectedNode.id) ;
      })
      .style("stroke", "#fdd13a")
      .style("stroke-width",2.0) 
      .style("opacity", 1.0)
    } else if (selectedNode.type === "proposal") {
      d3.selectAll("line").filter(function(d) {
          return (d.type === filter && d.target.id === selectedNode.id) ;
      })
      .style("stroke", "#fdd13a")
      .style("stroke-width",2.0) 
      .style("opacity", 1.0)
    }
  }

  createVisualization(network) {
    this.appendNodes(network.nodes);
    this.appendLinks(network.links);
    
    if (!this.initialized) {
      this.initialize();
    }
  }

  appendNodes(nodes){
    if (!nodes.length) { return }

    for (var i=0; i<nodes.length; i++) {
        this.nodesById[nodes[i].id] = [];
        this.graphNodes.push(nodes[i]);
    }
  }

  appendLinks(links){
    if (!links.length) { return }

    for (var i=0; i<links.length; i++) {
      this.graphLinks.push(links[i]);
    }
  }

  render() {
      return (
        <div ref={this.graphRef}>
          <svg id="network" ref={node => this.node = node}
            width={this.props.width} height={this.props.height}>
          </svg>
        </div>
      )
   }
}
