/**
 * D3.js Force-Directed Graph for Address Link Analysis
 * With expand/navigation functionality
 */

let graphState = {
    nodes: [],
    links: [],
    simulation: null,
    svg: null,
    g: null,
    chain: null,
    centralAddress: null,
    expandedNodes: new Set(),
    history: [],
    tooltip: null
};

function loadGraph(url, chain) {
    const container = document.getElementById('graph-container');
    const loading = document.getElementById('graph-loading');

    graphState.chain = chain;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            loading.style.display = 'none';
            if (data.nodes && data.nodes.length > 0) {
                graphState.centralAddress = data.central_address;
                graphState.nodes = data.nodes;
                graphState.links = data.links;
                graphState.expandedNodes.add(data.central_address.toLowerCase());
                graphState.history = [{
                    address: data.central_address,
                    label: shortenAddress(data.central_address)
                }];
                initGraph(container);
                updateBreadcrumbs();
            } else {
                container.innerHTML = '<div class="text-center py-5 text-muted">No connections found for this address</div>';
            }
        })
        .catch(error => {
            loading.style.display = 'none';
            container.innerHTML = '<div class="text-center py-5 text-danger">Error loading graph: ' + error.message + '</div>';
        });
}

function initGraph(container) {
    // Clear container
    container.innerHTML = '';

    // Add controls
    const controls = document.createElement('div');
    controls.id = 'graph-controls';
    controls.className = 'graph-controls p-2 bg-light border-bottom';
    controls.innerHTML = `
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div id="breadcrumbs" class="breadcrumbs d-flex align-items-center flex-wrap gap-1"></div>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-secondary" onclick="resetGraph()" title="Reset to original view">
                    <i class="bi bi-arrow-counterclockwise"></i> Reset
                </button>
                <button class="btn btn-outline-secondary" onclick="centerGraph()" title="Center view">
                    <i class="bi bi-arrows-fullscreen"></i> Center
                </button>
            </div>
        </div>
        <div class="mt-1 small text-muted">
            <i class="bi bi-info-circle"></i>
            <strong>Double-click</strong> a node to expand its connections |
            <strong>Single-click</strong> to navigate to address page
        </div>
    `;
    container.appendChild(controls);

    // Dimensions
    const width = container.clientWidth || 800;
    const height = 500;

    // Create SVG
    graphState.svg = d3.select(container)
        .append('svg')
        .attr('width', '100%')
        .attr('height', height)
        .attr('viewBox', [0, 0, width, height]);

    // Add zoom behavior
    graphState.g = graphState.svg.append('g');

    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            graphState.g.attr('transform', event.transform);
        });

    graphState.svg.call(zoom);

    // Store zoom for later use
    graphState.zoom = zoom;

    // Arrow markers
    graphState.svg.append('defs').selectAll('marker')
        .data(['arrow-out', 'arrow-in', 'arrow-token'])
        .enter().append('marker')
        .attr('id', d => d)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('fill', d => {
            if (d === 'arrow-out') return '#dc3545';
            if (d === 'arrow-in') return '#28a745';
            return '#6c757d';
        })
        .attr('d', 'M0,-5L10,0L0,5');

    // Tooltip
    if (graphState.tooltip) {
        graphState.tooltip.remove();
    }
    graphState.tooltip = d3.select('body').append('div')
        .attr('class', 'graph-tooltip')
        .style('position', 'absolute')
        .style('visibility', 'hidden')
        .style('background', 'rgba(0,0,0,0.85)')
        .style('color', '#fff')
        .style('padding', '10px 14px')
        .style('border-radius', '6px')
        .style('font-size', '12px')
        .style('max-width', '320px')
        .style('z-index', '1000')
        .style('box-shadow', '0 4px 12px rgba(0,0,0,0.3)');

    // Create simulation
    graphState.simulation = d3.forceSimulation(graphState.nodes)
        .force('link', d3.forceLink(graphState.links)
            .id(d => d.id)
            .distance(120))
        .force('charge', d3.forceManyBody().strength(-400))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => (d.size || 10) + 15));

    renderGraph();
    addLegend();
}

function renderGraph() {
    const g = graphState.g;

    // Clear existing elements
    g.selectAll('.links').remove();
    g.selectAll('.nodes').remove();

    // Create links
    const link = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(graphState.links)
        .enter().append('line')
        .attr('stroke', d => {
            if (d.type === 'token_transfer') return '#6c757d';
            if (d.direction === 'out') return '#dc3545';
            return '#28a745';
        })
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => {
            if (d.type === 'token_transfer') return 2;
            return Math.min(Math.max(1, Math.log((d.value || 0) + 1)), 5);
        })
        .attr('stroke-dasharray', d => d.type === 'token_transfer' ? '5,5' : null)
        .attr('marker-end', d => {
            if (d.type === 'token_transfer') return 'url(#arrow-token)';
            if (d.direction === 'out') return 'url(#arrow-out)';
            return 'url(#arrow-in)';
        });

    // Create nodes
    const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('g')
        .data(graphState.nodes)
        .enter().append('g')
        .attr('class', 'node')
        .style('cursor', 'pointer')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    // Node circles
    node.append('circle')
        .attr('r', d => d.size || 10)
        .attr('fill', d => getNodeColor(d))
        .attr('stroke', d => graphState.expandedNodes.has(d.id.toLowerCase()) ? '#ffc107' : '#fff')
        .attr('stroke-width', d => graphState.expandedNodes.has(d.id.toLowerCase()) ? 3 : 2);

    // Expand indicator for non-expanded nodes
    node.filter(d => !graphState.expandedNodes.has(d.id.toLowerCase()) && !d.is_central)
        .append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .attr('font-size', '10px')
        .attr('fill', '#fff')
        .attr('pointer-events', 'none')
        .text('+');

    // Node labels
    node.append('text')
        .attr('dy', d => (d.size || 10) + 15)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('fill', '#333')
        .attr('font-weight', d => d.is_central ? 'bold' : 'normal')
        .text(d => d.label);

    // Token badges
    node.filter(d => d.tokens && d.tokens.length > 0)
        .append('text')
        .attr('dy', d => (d.size || 10) + 26)
        .attr('text-anchor', 'middle')
        .attr('font-size', '8px')
        .attr('fill', '#6c757d')
        .text(d => d.tokens.slice(0, 3).join(', ') + (d.tokens.length > 3 ? '...' : ''));

    // Node interactions
    node.on('mouseover', function(event, d) {
            d3.select(this).select('circle')
                .attr('stroke', '#ffc107')
                .attr('stroke-width', 4);

            let tooltipContent = `<strong>${d.id}</strong><br>`;
            if (d.is_central) tooltipContent += `<span class="badge bg-primary">Central Address</span><br>`;
            if (graphState.expandedNodes.has(d.id.toLowerCase())) {
                tooltipContent += `<span class="badge bg-warning text-dark">Expanded</span><br>`;
            }
            if (d.tx_count) tooltipContent += `Transactions: ${d.tx_count}<br>`;
            if (d.value) tooltipContent += `Total Value: ${d.value.toFixed(4)}<br>`;
            if (d.tokens && d.tokens.length > 0) {
                tooltipContent += `Tokens: ${d.tokens.join(', ')}<br>`;
            }
            if (!graphState.expandedNodes.has(d.id.toLowerCase())) {
                tooltipContent += `<br><em>Double-click to expand</em>`;
            }

            graphState.tooltip.html(tooltipContent)
                .style('visibility', 'visible')
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px');
        })
        .on('mousemove', function(event) {
            graphState.tooltip.style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function(event, d) {
            d3.select(this).select('circle')
                .attr('stroke', graphState.expandedNodes.has(d.id.toLowerCase()) ? '#ffc107' : '#fff')
                .attr('stroke-width', graphState.expandedNodes.has(d.id.toLowerCase()) ? 3 : 2);
            graphState.tooltip.style('visibility', 'hidden');
        })
        .on('click', function(event, d) {
            // Single click - navigate to address page
            event.stopPropagation();
            window.location.href = `/address/${graphState.chain}/${d.id}`;
        })
        .on('dblclick', function(event, d) {
            // Double click - expand node
            event.stopPropagation();
            event.preventDefault();
            if (!graphState.expandedNodes.has(d.id.toLowerCase())) {
                expandNode(d.id);
            }
        });

    // Prevent single click when double clicking
    node.on('click', debounce(function(event, d) {
        window.location.href = `/address/${graphState.chain}/${d.id}`;
    }, 250));

    // Link hover
    link.on('mouseover', function(event, d) {
            d3.select(this)
                .attr('stroke-opacity', 1)
                .attr('stroke-width', 4);

            let tooltipContent = '';
            if (d.type === 'token_transfer') {
                tooltipContent = `<strong>Token Transfers</strong><br>`;
                tooltipContent += `Tokens: ${d.tokens.join(', ')}<br>`;
                tooltipContent += `Count: ${d.count}`;
            } else {
                tooltipContent = `<strong>Transaction</strong><br>`;
                tooltipContent += `Value: ${d.value ? d.value.toFixed(4) : 0} ${d.symbol || ''}`;
            }

            graphState.tooltip.html(tooltipContent)
                .style('visibility', 'visible')
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function(event, d) {
            d3.select(this)
                .attr('stroke-opacity', 0.6)
                .attr('stroke-width', d => {
                    if (d.type === 'token_transfer') return 2;
                    return Math.min(Math.max(1, Math.log((d.value || 0) + 1)), 5);
                });
            graphState.tooltip.style('visibility', 'hidden');
        });

    // Update positions on tick
    graphState.simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
}

function expandNode(address) {
    const existingNodeIds = graphState.nodes.map(n => n.id);

    // Show loading indicator on the node
    graphState.g.selectAll('.node')
        .filter(d => d.id.toLowerCase() === address.toLowerCase())
        .select('circle')
        .attr('stroke', '#17a2b8')
        .attr('stroke-width', 4)
        .attr('stroke-dasharray', '5,5');

    fetch(`/api/expand/${graphState.chain}/${address}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ existing_nodes: existingNodeIds })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Expand error:', data.error);
            return;
        }

        // Mark node as expanded
        graphState.expandedNodes.add(address.toLowerCase());

        // Add to history
        graphState.history.push({
            address: address,
            label: shortenAddress(address)
        });
        updateBreadcrumbs();

        // Add new nodes
        if (data.nodes && data.nodes.length > 0) {
            // Position new nodes near the expanded node
            const expandedNode = graphState.nodes.find(n => n.id.toLowerCase() === address.toLowerCase());
            const baseX = expandedNode ? expandedNode.x : 400;
            const baseY = expandedNode ? expandedNode.y : 250;

            data.nodes.forEach((node, i) => {
                const angle = (2 * Math.PI * i) / data.nodes.length;
                node.x = baseX + Math.cos(angle) * 100;
                node.y = baseY + Math.sin(angle) * 100;
                graphState.nodes.push(node);
            });
        }

        // Add new links
        if (data.links && data.links.length > 0) {
            data.links.forEach(link => {
                // Check if link already exists
                const exists = graphState.links.some(l =>
                    (l.source.id || l.source) === (link.source) &&
                    (l.target.id || l.target) === (link.target)
                );
                if (!exists) {
                    graphState.links.push(link);
                }
            });
        }

        // Update the expanded node's appearance
        const nodeToUpdate = graphState.nodes.find(n => n.id.toLowerCase() === address.toLowerCase());
        if (nodeToUpdate) {
            nodeToUpdate.is_expanded = true;
        }

        // Restart simulation with new data
        graphState.simulation.nodes(graphState.nodes);
        graphState.simulation.force('link').links(graphState.links);
        graphState.simulation.alpha(0.5).restart();

        // Re-render
        renderGraph();
    })
    .catch(error => {
        console.error('Failed to expand node:', error);
    });
}

function resetGraph() {
    // Reload the page to reset everything
    window.location.reload();
}

function centerGraph() {
    const container = document.getElementById('graph-container');
    const width = container.clientWidth || 800;
    const height = 500;

    graphState.svg.transition()
        .duration(500)
        .call(graphState.zoom.transform, d3.zoomIdentity.translate(0, 0).scale(1));
}

function updateBreadcrumbs() {
    const breadcrumbs = document.getElementById('breadcrumbs');
    if (!breadcrumbs) return;

    let html = '<span class="text-muted me-2"><i class="bi bi-diagram-3"></i> Path:</span>';

    graphState.history.forEach((item, index) => {
        if (index > 0) {
            html += '<i class="bi bi-chevron-right text-muted mx-1"></i>';
        }
        const isLast = index === graphState.history.length - 1;
        if (isLast) {
            html += `<span class="badge bg-primary">${item.label}</span>`;
        } else {
            html += `<a href="/address/${graphState.chain}/${item.address}" class="badge bg-secondary text-decoration-none">${item.label}</a>`;
        }
    });

    breadcrumbs.innerHTML = html;
}

function addLegend() {
    const legend = graphState.svg.append('g')
        .attr('class', 'legend')
        .attr('transform', 'translate(20, 20)');

    const legendData = [
        { label: 'Central Address', color: '#0d6efd' },
        { label: 'Expanded Node', color: '#6c757d', stroke: '#ffc107' },
        { label: 'Unexpanded (dbl-click)', color: '#6c757d' },
        { label: 'Outgoing TX', color: '#dc3545', line: true },
        { label: 'Incoming TX', color: '#28a745', line: true },
        { label: 'Token Transfer', color: '#6c757d', line: true, dashed: true }
    ];

    legendData.forEach((item, i) => {
        const g = legend.append('g')
            .attr('transform', `translate(0, ${i * 20})`);

        if (item.line) {
            g.append('line')
                .attr('x1', 0)
                .attr('y1', 10)
                .attr('x2', 20)
                .attr('y2', 10)
                .attr('stroke', item.color)
                .attr('stroke-width', 2)
                .attr('stroke-dasharray', item.dashed ? '5,5' : null);
        } else {
            g.append('circle')
                .attr('cx', 10)
                .attr('cy', 10)
                .attr('r', 8)
                .attr('fill', item.color)
                .attr('stroke', item.stroke || '#fff')
                .attr('stroke-width', item.stroke ? 2 : 1);
        }

        g.append('text')
            .attr('x', 30)
            .attr('y', 14)
            .attr('font-size', '11px')
            .attr('fill', '#666')
            .text(item.label);
    });
}

function getNodeColor(d) {
    if (d.is_central) return '#0d6efd';
    if (graphState.expandedNodes.has(d.id.toLowerCase())) return '#17a2b8';
    return '#6c757d';
}

function shortenAddress(address) {
    if (address && address.length > 10) {
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    }
    return address || '';
}

function debounce(func, wait) {
    let timeout;
    let clickCount = 0;

    return function executedFunction(event, d) {
        clickCount++;
        const currentCount = clickCount;

        clearTimeout(timeout);
        timeout = setTimeout(() => {
            if (currentCount === clickCount) {
                // Only execute if this was a single click (not followed by another click)
                if (clickCount === 1) {
                    func(event, d);
                }
            }
            clickCount = 0;
        }, wait);
    };
}

// Drag functions
function dragstarted(event, d) {
    if (!event.active) graphState.simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active) graphState.simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}
