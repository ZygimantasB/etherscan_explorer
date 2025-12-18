/**
 * D3.js Force-Directed Graph for Address Link Analysis
 */

function loadGraph(url, chain) {
    const container = document.getElementById('graph-container');
    const loading = document.getElementById('graph-loading');

    fetch(url)
        .then(response => response.json())
        .then(data => {
            loading.style.display = 'none';
            if (data.nodes && data.nodes.length > 0) {
                renderGraph(container, data, chain);
            } else {
                container.innerHTML = '<div class="text-center py-5 text-muted">No connections found for this address</div>';
            }
        })
        .catch(error => {
            loading.style.display = 'none';
            container.innerHTML = '<div class="text-center py-5 text-danger">Error loading graph: ' + error.message + '</div>';
        });
}

function renderGraph(container, data, chain) {
    // Clear container
    container.innerHTML = '';

    // Dimensions
    const width = container.clientWidth || 800;
    const height = 500;

    // Create SVG
    const svg = d3.select(container)
        .append('svg')
        .attr('width', '100%')
        .attr('height', height)
        .attr('viewBox', [0, 0, width, height]);

    // Add zoom behavior
    const g = svg.append('g');

    const zoom = d3.zoom()
        .scaleExtent([0.2, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });

    svg.call(zoom);

    // Arrow marker for directed edges
    svg.append('defs').selectAll('marker')
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

    // Color scale for nodes
    const colorScale = d3.scaleOrdinal()
        .domain(['central', 'address'])
        .range(['#0d6efd', '#6c757d']);

    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.links)
            .id(d => d.id)
            .distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => d.size + 10));

    // Create links
    const link = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(data.links)
        .enter().append('line')
        .attr('stroke', d => {
            if (d.type === 'token_transfer') return '#6c757d';
            if (d.direction === 'out') return '#dc3545';
            return '#28a745';
        })
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => {
            if (d.type === 'token_transfer') return 2;
            return Math.min(Math.max(1, Math.log(d.value + 1)), 5);
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
        .data(data.nodes)
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
        .attr('fill', d => d.is_central ? '#0d6efd' : '#6c757d')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);

    // Node labels
    node.append('text')
        .attr('dy', d => (d.size || 10) + 15)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('fill', '#333')
        .text(d => d.label);

    // Token badges for nodes with token interactions
    node.filter(d => d.tokens && d.tokens.length > 0)
        .append('text')
        .attr('dy', d => (d.size || 10) + 26)
        .attr('text-anchor', 'middle')
        .attr('font-size', '8px')
        .attr('fill', '#6c757d')
        .text(d => d.tokens.slice(0, 3).join(', ') + (d.tokens.length > 3 ? '...' : ''));

    // Tooltip
    const tooltip = d3.select('body').append('div')
        .attr('class', 'graph-tooltip')
        .style('position', 'absolute')
        .style('visibility', 'hidden')
        .style('background', 'rgba(0,0,0,0.8)')
        .style('color', '#fff')
        .style('padding', '10px')
        .style('border-radius', '5px')
        .style('font-size', '12px')
        .style('max-width', '300px')
        .style('z-index', '1000');

    // Node interactions
    node.on('mouseover', function(event, d) {
            d3.select(this).select('circle')
                .attr('stroke', '#ffc107')
                .attr('stroke-width', 3);

            let tooltipContent = `<strong>${d.id}</strong><br>`;
            if (d.tx_count) tooltipContent += `Transactions: ${d.tx_count}<br>`;
            if (d.value) tooltipContent += `Total Value: ${d.value.toFixed(4)}<br>`;
            if (d.tokens && d.tokens.length > 0) {
                tooltipContent += `Tokens: ${d.tokens.join(', ')}`;
            }

            tooltip.html(tooltipContent)
                .style('visibility', 'visible')
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px');
        })
        .on('mousemove', function(event) {
            tooltip.style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function() {
            d3.select(this).select('circle')
                .attr('stroke', '#fff')
                .attr('stroke-width', 2);
            tooltip.style('visibility', 'hidden');
        })
        .on('click', function(event, d) {
            if (!d.is_central) {
                window.location.href = `/address/${chain}/${d.id}`;
            }
        });

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

            tooltip.html(tooltipContent)
                .style('visibility', 'visible')
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function(event, d) {
            d3.select(this)
                .attr('stroke-opacity', 0.6)
                .attr('stroke-width', d => {
                    if (d.type === 'token_transfer') return 2;
                    return Math.min(Math.max(1, Math.log(d.value + 1)), 5);
                });
            tooltip.style('visibility', 'hidden');
        });

    // Update positions on tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    // Legend
    const legend = svg.append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(20, 20)`);

    const legendData = [
        { label: 'Central Address', color: '#0d6efd' },
        { label: 'Related Address', color: '#6c757d' },
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
                .attr('fill', item.color);
        }

        g.append('text')
            .attr('x', 30)
            .attr('y', 14)
            .attr('font-size', '11px')
            .attr('fill', '#666')
            .text(item.label);
    });
}
