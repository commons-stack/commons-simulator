class ForceGraph {
  constructor(svg) {
    this.width = svg.attr("width");
    this.height = svg.attr("height");
    this.svg = svg;

    this.graphNodes = [];
    this.graphLinks = [];
    //for convenience; this may (or should) be "merged" with graphNodes
    this.nodesById = {};
    this.connsById = {};

    this.nodeRadius = 16;
    this.color = d3.scaleOrdinal(d3.schemeAccent);
  }

  linkDistance(d) {
    return Math.floor(Math.random() * 11) + 160;
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

    simulation = this.simulation = d3.forceSimulation(self.graphNodes)
        .force("link", d3.forceLink(self.graphLinks).id(function(d) { return d.id; }))
        .force("charge_force", d3.forceManyBody())
        .force("center_force", d3.forceCenter(self.width / 2, self.height / 2))
        //.force("x", d3.forceX())
        //.force("y", d3.forceY())
        .alphaDecay(0)
        .alphaMin(0)     
        .on("tick", function(){ self.tickActions(self.nodeCollection, self.linkCollection) });

      this.setupNodes();
      this.setupLinks();

    //simulation.force("link")
    //    .links(this.graphLinks);
        //.distance(function(l,i){return 80;});
        //.distance(self.linkDistance);

    this.initialized = true;
  }


  setupNodes() {
    let self = this;
    this.nodeCollection = this.svg.append("g")
        .attr("class", "nodes")
        .selectAll("circle")
        .data(this.graphNodes)
        .enter()
        .append("circle")
        .attr("r", this.nodeRadius)
        .attr("fill","#ae81ff")
        .attr("stroke", "#fff").attr("stroke-width", 1.5)
          .call(d3.drag()
              .on("start", function(d){ self.dragstarted(self.simulation, d); } )
              .on("drag", function(d){ self.dragged(d); } )
              .on("end", function(d){ self.dragended(self.simulation, d); } ))  
  }

  setupLinks(){
    this.linkCollection = this.svg.append("g")
        .attr("class", "links")
        .selectAll(".link")
        .enter()
        .append("line")
        .attr("stroke", "#808080")
        .attr("stroke-width", 1.5)
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
    


  createVisualisation(newNodes,newLinks) {
    this.appendNodes(newNodes);
    this.appendLinks(newLinks);
    
    if (!this.initialized) {
      this.initialize();
    }

   this.restartSimulation();
  }

  restartSimulation() {
    // Update and restart the simulation.
    var self = this;
    // Apply the general update pattern to the nodes.
      this.nodeCollection = this.nodeCollection.data(this.graphNodes);
      // Apply class "existing-node" to all existing nodes
      this.nodeCollection.attr("fill","#ae81ff");
      // Remove all old nodes
      // Apply to all new nodes (enter selection)
      this.nodeCollection = this.nodeCollection
          .enter()
          .append("circle")
          .attr("fill", "#46bc99")
          .attr("r", this.nodeRadius)
          .call(d3.drag()
              .on("start", function(d){ self.dragstarted(self.simulation, d); } )
              .on("drag", function(d){ self.dragged(d); } )
              .on("end", function(d){ self.dragended(self.simulation, d); } ))  
          .merge(this.nodeCollection);

      // Apply the general update pattern to the links.
      this.linkCollection = this.linkCollection.data(this.graphLinks);
      this.linkCollection = this.linkCollection
          .enter()
          .append("line")
          .attr("stroke", "#808080")
          .attr("stroke-width", 1.5)
          .on("click", function(d) {
          })
          .merge(this.linkCollection);

    //this.linkCollection.attr("stroke-width", function(d) { return 1.5 + ((parseInt(self.connsById[d.id].msgCount / 3) -1) / 2)  }); //increase in steps of 0.5

    this.simulation.nodes(self.graphNodes);            
    this.simulation.force("link").links(self.graphLinks);
    //this.simulation.force("center", d3.forceCenter(self.width/2, self.height/2));
    this.simulation.alpha(1).restart();

  }

  appendNodes(nodes){
    if (!nodes.length) { return }

    for (var i=0; i<nodes.length; i++) {
      nodes[i].id = i;
        this.nodesById[nodes[i].id] = [];
        this.graphNodes.push(nodes[i]);
    }
  }

  appendLinks(links){
    if (!links.length) { return }

    for (var i=0;i<links.length;i++) {
      links[i].id    = links[i].source + "-" + links[i].target;
      let source = links[i].source;
      let target = links[i].target;

      /*
      this.nodesById[target].push(id);
      this.nodesById[source].push(id);

      this.connsById[id] = {};
      this.connsById[id].target   = links[i].target;
      this.connsById[id].source   = links[i].source;
      */
      this.graphLinks.push(links[i]);
    }
  }
}
