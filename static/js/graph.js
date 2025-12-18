/**
 * D3.js Force-Directed Graph for Address Link Analysis
 * With expand functionality and popup details modal
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
    selectedNode: null,
    tooltip: null,
    width: 800,
    height: 500
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
                initGraph(container);
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
            <div class="d-flex align-items-center gap-2">
                <span class="text-muted small"><i class="bi bi-diagram-3"></i> Nodes: <strong id="node-count">${graphState.nodes.length}</strong></span>
                <span class="text-muted small">| Links: <strong id="link-count">${graphState.links.length}</strong></span>
            </div>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-secondary" onclick="resetGraph()" title="Reset to original view">
                    <i class="bi bi-arrow-counterclockwise"></i> Reset
                </button>
                <button class="btn btn-outline-secondary" onclick="centerGraph()" title="Center view">
                    <i class="bi bi-arrows-fullscreen"></i> Center
                </button>
                <button class="btn btn-outline-secondary" onclick="expandAllVisible()" title="Expand all visible nodes">
                    <i class="bi bi-arrows-expand"></i> Expand All
                </button>
            </div>
        </div>
        <div class="mt-1 small text-muted">
            <i class="bi bi-info-circle"></i>
            <strong>Click</strong> node to select |
            <strong>Double-click</strong> to expand connections |
            Drag to move nodes
        </div>
    `;
    container.appendChild(controls);

    // Add details modal overlay
    const modalOverlay = document.createElement('div');
    modalOverlay.id = 'graph-modal-overlay';
    modalOverlay.className = 'graph-modal-overlay';
    modalOverlay.onclick = function(e) { if (e.target === this) closeDetailsModal(); };
    modalOverlay.innerHTML = `
        <div class="graph-modal-dialog">
            <div class="graph-modal-header">
                <h5 class="mb-0"><i class="bi bi-wallet2"></i> <span id="modal-title">Address Details</span></h5>
                <button type="button" class="btn-close btn-close-white" onclick="closeDetailsModal()"></button>
            </div>
            <div class="graph-modal-body" id="modal-body-content">
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-2 text-muted">Loading details...</p>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modalOverlay);

    // Add modal styles if not present
    if (!document.getElementById('graph-modal-styles')) {
        const styles = document.createElement('style');
        styles.id = 'graph-modal-styles';
        styles.textContent = `
            .graph-modal-overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.7);
                z-index: 9999;
                justify-content: center;
                align-items: center;
            }
            .graph-modal-overlay.show {
                display: flex;
            }
            .graph-modal-dialog {
                background: #1a1a2e;
                border-radius: 12px;
                width: 90%;
                max-width: 700px;
                max-height: 85vh;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0,0,0,0.5);
                animation: modalSlideIn 0.3s ease;
            }
            @keyframes modalSlideIn {
                from { transform: translateY(-20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            .graph-modal-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 16px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                color: white;
            }
            .graph-modal-body {
                padding: 20px;
                overflow-y: auto;
                max-height: calc(85vh - 60px);
                color: #e0e0e0;
            }
            .detail-card {
                background: #252542;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }
            .detail-card h6 {
                color: #9d9dff;
                margin-bottom: 12px;
                font-size: 0.9rem;
            }
            .detail-row {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #333355;
            }
            .detail-row:last-child {
                border-bottom: none;
            }
            .detail-label {
                color: #888;
            }
            .detail-value {
                color: #fff;
                font-weight: 500;
            }
            .token-badge {
                display: inline-block;
                background: #333355;
                padding: 4px 10px;
                border-radius: 20px;
                margin: 3px;
                font-size: 0.8rem;
            }
            .modal-btn-group {
                display: flex;
                gap: 10px;
                margin-top: 15px;
            }
            .modal-btn {
                flex: 1;
                padding: 10px 15px;
                border-radius: 6px;
                border: none;
                cursor: pointer;
                font-weight: 500;
                transition: all 0.2s;
            }
            .modal-btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .modal-btn-secondary {
                background: #333355;
                color: #e0e0e0;
            }
            .modal-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            .tx-list {
                max-height: 200px;
                overflow-y: auto;
            }
            .tx-item {
                background: #1e1e3f;
                padding: 10px;
                border-radius: 6px;
                margin-bottom: 8px;
                font-size: 0.85rem;
            }
            .tx-item .hash {
                color: #667eea;
                font-family: monospace;
            }
            .tx-item .value {
                color: #4ade80;
            }
            .tx-item .direction-in { color: #4ade80; }
            .tx-item .direction-out { color: #f87171; }
        `;
        document.head.appendChild(styles);
    }

    // Selected node info panel (side panel)
    const infoPanel = document.createElement('div');
    infoPanel.id = 'node-info-panel';
    infoPanel.className = 'd-none position-absolute bg-dark text-light border rounded shadow p-3';
    infoPanel.style.cssText = 'right: 10px; top: 60px; width: 260px; z-index: 100; max-height: 350px; overflow-y: auto;';
    container.appendChild(infoPanel);

    // Dimensions
    graphState.width = container.clientWidth || 800;
    graphState.height = 500;

    // Create SVG
    graphState.svg = d3.select(container)
        .append('svg')
        .attr('width', '100%')
        .attr('height', graphState.height)
        .attr('viewBox', [0, 0, graphState.width, graphState.height])
        .style('background', '#fafafa');

    // Add zoom behavior
    graphState.g = graphState.svg.append('g');

    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            graphState.g.attr('transform', event.transform);
        });

    graphState.svg.call(zoom);
    graphState.zoom = zoom;

    // Click on background to deselect
    graphState.svg.on('click', function(event) {
        if (event.target.tagName === 'svg') {
            deselectNode();
        }
    });

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
        .style('padding', '8px 12px')
        .style('border-radius', '6px')
        .style('font-size', '11px')
        .style('max-width', '280px')
        .style('z-index', '1000')
        .style('pointer-events', 'none');

    // Create simulation
    graphState.simulation = d3.forceSimulation(graphState.nodes)
        .force('link', d3.forceLink(graphState.links)
            .id(d => d.id)
            .distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(graphState.width / 2, graphState.height / 2))
        .force('collision', d3.forceCollide().radius(d => (d.size || 10) + 10));

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
        .attr('stroke-opacity', 0.5)
        .attr('stroke-width', d => {
            if (d.type === 'token_transfer') return 1.5;
            return Math.min(Math.max(1, Math.log((d.value || 0) + 1)), 4);
        })
        .attr('stroke-dasharray', d => d.type === 'token_transfer' ? '4,4' : null)
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
        .attr('stroke', d => {
            if (graphState.selectedNode && graphState.selectedNode.id === d.id) return '#ffc107';
            if (graphState.expandedNodes.has(d.id.toLowerCase())) return '#17a2b8';
            return '#fff';
        })
        .attr('stroke-width', d => {
            if (graphState.selectedNode && graphState.selectedNode.id === d.id) return 4;
            if (graphState.expandedNodes.has(d.id.toLowerCase())) return 3;
            return 2;
        });

    // Expand indicator (+ sign) for non-expanded nodes
    node.filter(d => !graphState.expandedNodes.has(d.id.toLowerCase()))
        .append('text')
        .attr('class', 'expand-indicator')
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .attr('font-size', '12px')
        .attr('font-weight', 'bold')
        .attr('fill', '#fff')
        .attr('pointer-events', 'none')
        .text('+');

    // Checkmark for expanded nodes
    node.filter(d => graphState.expandedNodes.has(d.id.toLowerCase()) && !d.is_central)
        .append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .attr('font-size', '10px')
        .attr('fill', '#fff')
        .attr('pointer-events', 'none')
        .text('✓');

    // Node labels
    node.append('text')
        .attr('dy', d => (d.size || 10) + 14)
        .attr('text-anchor', 'middle')
        .attr('font-size', '9px')
        .attr('fill', '#333')
        .attr('font-weight', d => d.is_central ? 'bold' : 'normal')
        .text(d => d.label || shortenAddress(d.id));

    // Node interactions
    node.on('mouseover', function(event, d) {
            if (graphState.selectedNode && graphState.selectedNode.id === d.id) return;

            d3.select(this).select('circle')
                .attr('stroke', '#ffc107')
                .attr('stroke-width', 3);

            let tooltipContent = `<strong>${shortenAddress(d.id)}</strong>`;
            if (!graphState.expandedNodes.has(d.id.toLowerCase())) {
                tooltipContent += `<br><em style="color: #ffc107;">Double-click to expand</em>`;
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
            if (graphState.selectedNode && graphState.selectedNode.id === d.id) return;

            d3.select(this).select('circle')
                .attr('stroke', graphState.expandedNodes.has(d.id.toLowerCase()) ? '#17a2b8' : '#fff')
                .attr('stroke-width', graphState.expandedNodes.has(d.id.toLowerCase()) ? 3 : 2);
            graphState.tooltip.style('visibility', 'hidden');
        })
        .on('click', function(event, d) {
            event.stopPropagation();
            selectNode(d);
        })
        .on('dblclick', function(event, d) {
            event.stopPropagation();
            event.preventDefault();
            graphState.tooltip.style('visibility', 'hidden');
            if (!graphState.expandedNodes.has(d.id.toLowerCase())) {
                expandNode(d.id);
            }
        });

    // Link hover
    link.on('mouseover', function(event, d) {
            d3.select(this)
                .attr('stroke-opacity', 1)
                .attr('stroke-width', 4);

            let tooltipContent = '';
            if (d.type === 'token_transfer') {
                tooltipContent = `<strong>Token Transfer</strong><br>`;
                if (d.tokens) tooltipContent += `Tokens: ${d.tokens.join(', ')}<br>`;
                if (d.count) tooltipContent += `Count: ${d.count}`;
            } else {
                tooltipContent = `<strong>${d.direction === 'out' ? 'Outgoing' : 'Incoming'}</strong><br>`;
                tooltipContent += `Value: ${d.value ? d.value.toFixed(4) : 0} ${d.symbol || ''}`;
            }

            graphState.tooltip.html(tooltipContent)
                .style('visibility', 'visible')
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function(event, d) {
            d3.select(this)
                .attr('stroke-opacity', 0.5)
                .attr('stroke-width', d => {
                    if (d.type === 'token_transfer') return 1.5;
                    return Math.min(Math.max(1, Math.log((d.value || 0) + 1)), 4);
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

    // Update counts
    updateCounts();
}

function selectNode(d) {
    graphState.selectedNode = d;

    // Update visual selection
    graphState.g.selectAll('.node circle')
        .attr('stroke', node => {
            if (node.id === d.id) return '#ffc107';
            if (graphState.expandedNodes.has(node.id.toLowerCase())) return '#17a2b8';
            return '#fff';
        })
        .attr('stroke-width', node => {
            if (node.id === d.id) return 4;
            if (graphState.expandedNodes.has(node.id.toLowerCase())) return 3;
            return 2;
        });

    // Highlight connected links
    graphState.g.selectAll('.links line')
        .attr('stroke-opacity', link => {
            const sourceId = link.source.id || link.source;
            const targetId = link.target.id || link.target;
            if (sourceId === d.id || targetId === d.id) return 1;
            return 0.2;
        });

    // Show side panel
    showNodeInfo(d);
}

function deselectNode() {
    graphState.selectedNode = null;

    // Reset visual selection
    graphState.g.selectAll('.node circle')
        .attr('stroke', d => graphState.expandedNodes.has(d.id.toLowerCase()) ? '#17a2b8' : '#fff')
        .attr('stroke-width', d => graphState.expandedNodes.has(d.id.toLowerCase()) ? 3 : 2);

    // Reset link opacity
    graphState.g.selectAll('.links line')
        .attr('stroke-opacity', 0.5);

    // Hide info panel
    document.getElementById('node-info-panel').classList.add('d-none');
}

function showNodeInfo(d) {
    const panel = document.getElementById('node-info-panel');
    const isExpanded = graphState.expandedNodes.has(d.id.toLowerCase());

    // Count connections
    const connections = graphState.links.filter(l => {
        const sourceId = l.source.id || l.source;
        const targetId = l.target.id || l.target;
        return sourceId === d.id || targetId === d.id;
    });

    let html = `
        <div class="d-flex justify-content-between align-items-start mb-2">
            <strong class="text-break" style="font-size: 11px;">${shortenAddress(d.id)}</strong>
            <button class="btn btn-sm btn-close btn-close-white" onclick="deselectNode()"></button>
        </div>
        <div class="mb-2">
            ${d.is_central ? '<span class="badge bg-primary me-1">Central</span>' : ''}
            ${isExpanded ? '<span class="badge bg-info me-1">Expanded</span>' : '<span class="badge bg-secondary me-1">Not Expanded</span>'}
        </div>
        <div class="small mb-2">
            <div><strong>Connections:</strong> ${connections.length}</div>
            ${d.tx_count ? `<div><strong>Transactions:</strong> ${d.tx_count}</div>` : ''}
            ${d.value ? `<div><strong>Total Value:</strong> ${d.value.toFixed(4)}</div>` : ''}
        </div>
        <div class="d-grid gap-2">
            ${!isExpanded ? `
                <button class="btn btn-sm btn-primary" onclick="expandNode('${d.id}')">
                    <i class="bi bi-arrows-expand"></i> Expand Connections
                </button>
            ` : ''}
            <button class="btn btn-sm btn-info" onclick="openDetailsModal('${d.id}')">
                <i class="bi bi-eye"></i> View Full Details
            </button>
            <button class="btn btn-sm btn-outline-light" onclick="copyToClipboard('${d.id}')">
                <i class="bi bi-clipboard"></i> Copy Address
            </button>
        </div>
    `;

    panel.innerHTML = html;
    panel.classList.remove('d-none');
}

function openDetailsModal(address) {
    const overlay = document.getElementById('graph-modal-overlay');
    const modalBody = document.getElementById('modal-body-content');
    const modalTitle = document.getElementById('modal-title');

    modalTitle.textContent = shortenAddress(address);
    overlay.classList.add('show');

    // Show loading
    modalBody.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2 text-muted">Loading comprehensive address details...</p>
            <small class="text-muted">Fetching from all APIs...</small>
        </div>
    `;

    // Fetch address details from ALL available endpoints
    const chain = graphState.chain;
    Promise.all([
        fetch(`/api/reputation/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/wallet-profile/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/graph/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/analytics/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/pnl/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/mev/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/approvals/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/whale-tracker/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/flash-loans/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/sniper-detection/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/copy-trading/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/funding-flow/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/liquidity-pools/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/governance/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/clustering/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/smartmoney/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/airdrops/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/gas-optimizer/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/ens/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/security-scan/${chain}/${address}`).then(r => r.json()).catch(() => null),
        fetch(`/api/token-transfers/${chain}/${address}`).then(r => r.json()).catch(() => null)
    ])
    .then(([reputation, profile, graphData, analytics, pnl, mev, approvals, whale, flashLoans, sniper, copyTrading, fundingFlow, liquidity, governance, clustering, smartMoney, airdrops, gasOptimizer, ens, security, tokenTransfers]) => {
        let html = '';

        // Address header with quick stats
        html += `
            <div class="detail-card">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0"><i class="bi bi-wallet2"></i> Address</h6>
                    <button class="btn btn-sm btn-outline-light" onclick="copyToClipboard('${address}')">
                        <i class="bi bi-clipboard"></i> Copy
                    </button>
                </div>
                <div style="font-family: monospace; font-size: 0.75rem; word-break: break-all; color: #667eea; background: #1e1e3f; padding: 10px; border-radius: 6px;">
                    ${address}
                </div>
            </div>
        `;

        // Wallet Profile & Classification
        if (profile && !profile.error) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-person-badge"></i> Wallet Profile</h6>
                    <div class="text-center mb-3">
                        <span class="badge bg-primary" style="font-size: 1.1rem; padding: 8px 16px;">
                            ${profile.classification || 'Unknown'}
                        </span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Activity Score</span>
                        <span class="detail-value">${profile.activity_score || 0}/100</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Total Transactions</span>
                        <span class="detail-value">${(profile.total_transactions || 0).toLocaleString()}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Unique Interactions</span>
                        <span class="detail-value">${profile.unique_interactions || 0}</span>
                    </div>
                    ${profile.first_tx_date ? `
                    <div class="detail-row">
                        <span class="detail-label">First Transaction</span>
                        <span class="detail-value">${profile.first_tx_date}</span>
                    </div>
                    ` : ''}
                    ${profile.avg_tx_value ? `
                    <div class="detail-row">
                        <span class="detail-label">Avg TX Value</span>
                        <span class="detail-value">${profile.avg_tx_value.toFixed(4)} ETH</span>
                    </div>
                    ` : ''}
                    ${profile.behaviors && profile.behaviors.length > 0 ? `
                    <div class="mt-2">
                        <small class="text-muted">Behaviors:</small><br>
                        ${profile.behaviors.map(b => `<span class="token-badge">${b}</span>`).join('')}
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Reputation Score
        if (reputation && !reputation.error && reputation.score) {
            // Handle nested score object structure
            const scoreData = reputation.score;
            const actualScore = typeof scoreData === 'object' ? (scoreData.score || 0) : scoreData;
            const breakdown = typeof scoreData === 'object' ? scoreData.breakdown : reputation.breakdown;
            const tier = typeof scoreData === 'object' ? scoreData.tier : null;
            const tierColor = typeof scoreData === 'object' ? scoreData.tier_color : null;
            const factors = typeof scoreData === 'object' ? scoreData.factors : null;

            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-star-fill"></i> Reputation Score</h6>
                    <div class="text-center mb-3">
                        <div style="font-size: 3rem; font-weight: bold; color: ${actualScore >= 70 ? '#4ade80' : actualScore >= 40 ? '#fbbf24' : '#f87171'};">
                            ${actualScore}
                        </div>
                        <small class="text-muted">out of 100</small>
                        ${tier ? `<div class="mt-1"><span class="badge bg-${tierColor || 'secondary'}">${tier}</span></div>` : ''}
                    </div>
                    ${breakdown ? `
                    <div class="detail-row">
                        <span class="detail-label">Age</span>
                        <span class="detail-value">${breakdown.age || breakdown.age_score || 0}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Transactions</span>
                        <span class="detail-value">${breakdown.transactions || breakdown.activity_score || 0}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Balance</span>
                        <span class="detail-value">${breakdown.balance || 0}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Token Diversity</span>
                        <span class="detail-value">${breakdown.token_diversity || 0}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">DeFi Usage</span>
                        <span class="detail-value">${breakdown.defi || breakdown.defi_score || 0}</span>
                    </div>
                    ${breakdown.risk_penalty ? `
                    <div class="detail-row">
                        <span class="detail-label" style="color: #f87171;">Risk Penalty</span>
                        <span class="detail-value" style="color: #f87171;">${breakdown.risk_penalty}</span>
                    </div>
                    ` : ''}
                    ` : ''}
                    ${factors && factors.length > 0 ? `
                    <div class="mt-2">
                        <small class="text-muted">Factors:</small><br>
                        ${factors.map(f => `<span class="token-badge" style="background: #333355;">${f}</span>`).join('')}
                    </div>
                    ` : ''}
                    ${reputation.badges && reputation.badges.length > 0 ? `
                    <div class="mt-2">
                        <small class="text-muted">Badges:</small><br>
                        ${reputation.badges.map(badge => `<span class="token-badge">${badge}</span>`).join('')}
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Analytics - Activity Summary
        if (analytics && !analytics.error) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-graph-up"></i> Activity Analytics</h6>
                    ${analytics.total_transactions ? `
                    <div class="detail-row">
                        <span class="detail-label">Total Transactions</span>
                        <span class="detail-value">${analytics.total_transactions.toLocaleString()}</span>
                    </div>
                    ` : ''}
                    ${analytics.active_days ? `
                    <div class="detail-row">
                        <span class="detail-label">Active Days</span>
                        <span class="detail-value">${analytics.active_days}</span>
                    </div>
                    ` : ''}
                    ${analytics.most_active_hour !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Most Active Hour</span>
                        <span class="detail-value">${analytics.most_active_hour}:00 UTC</span>
                    </div>
                    ` : ''}
                    ${analytics.token_distribution && analytics.token_distribution.length > 0 ? `
                    <div class="mt-2">
                        <small class="text-muted">Top Tokens:</small><br>
                        ${analytics.token_distribution.slice(0, 5).map(t => `
                            <span class="token-badge">${t.symbol}: ${t.percentage ? t.percentage.toFixed(1) : 0}%</span>
                        `).join('')}
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // P&L (Profit/Loss)
        if (pnl && !pnl.error) {
            const totalPnL = pnl.total_pnl || pnl.realized_pnl || 0;
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-currency-dollar"></i> Profit & Loss</h6>
                    <div class="text-center mb-3">
                        <div style="font-size: 1.8rem; font-weight: bold; color: ${totalPnL >= 0 ? '#4ade80' : '#f87171'};">
                            ${totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(4)} ETH
                        </div>
                    </div>
                    ${pnl.total_bought !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Total Bought</span>
                        <span class="detail-value">${pnl.total_bought.toFixed(4)} ETH</span>
                    </div>
                    ` : ''}
                    ${pnl.total_sold !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Total Sold</span>
                        <span class="detail-value">${pnl.total_sold.toFixed(4)} ETH</span>
                    </div>
                    ` : ''}
                    ${pnl.win_rate !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Win Rate</span>
                        <span class="detail-value">${(pnl.win_rate * 100).toFixed(1)}%</span>
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // ERC-20 Token Transfers
        if (tokenTransfers && !tokenTransfers.error && tokenTransfers.transfers && tokenTransfers.transfers.length > 0) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-coin"></i> ERC-20 Token Transfers</h6>
                    <div class="detail-row">
                        <span class="detail-label">Total Transfers</span>
                        <span class="detail-value">${tokenTransfers.total_transfers || tokenTransfers.transfers.length}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Unique Tokens</span>
                        <span class="detail-value">${tokenTransfers.unique_tokens || 0}</span>
                    </div>
                    ${tokenTransfers.tokens_sent && tokenTransfers.tokens_sent.length > 0 ? `
                    <div class="mt-3" style="background: #2d1f1f; border-radius: 8px; padding: 12px;">
                        <div class="d-flex align-items-center mb-2">
                            <i class="bi bi-arrow-up-right" style="color: #f87171; margin-right: 8px;"></i>
                            <strong style="color: #f87171;">Tokens Sent</strong>
                        </div>
                        ${tokenTransfers.tokens_sent.slice(0, 8).map(t => `
                            <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #3d2f2f;">
                                <div>
                                    <strong style="color: #fff;">${t.symbol}</strong>
                                    ${t.name && t.name !== 'Unknown Token' ? `<br><small style="color: #888;">${t.name}</small>` : ''}
                                </div>
                                <div style="text-align: right; color: #f87171; font-weight: 500;">
                                    ${formatTokenAmount(t.amount)}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    ` : ''}
                    ${tokenTransfers.tokens_received && tokenTransfers.tokens_received.length > 0 ? `
                    <div class="mt-3" style="background: #1f2d1f; border-radius: 8px; padding: 12px;">
                        <div class="d-flex align-items-center mb-2">
                            <i class="bi bi-arrow-down-left" style="color: #4ade80; margin-right: 8px;"></i>
                            <strong style="color: #4ade80;">Tokens Received</strong>
                        </div>
                        ${tokenTransfers.tokens_received.slice(0, 8).map(t => `
                            <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #2f3d2f;">
                                <div>
                                    <strong style="color: #fff;">${t.symbol}</strong>
                                    ${t.name && t.name !== 'Unknown Token' ? `<br><small style="color: #888;">${t.name}</small>` : ''}
                                </div>
                                <div style="text-align: right; color: #4ade80; font-weight: 500;">
                                    ${formatTokenAmount(t.amount)}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    ` : ''}
                    <div class="mt-3">
                        <strong class="text-muted">Recent Transfers:</strong>
                        <div class="tx-list" style="max-height: 300px; margin-top: 10px;">
                            ${tokenTransfers.transfers.slice(0, 20).map(tx => `
                                <div class="tx-item" style="border-left: 3px solid ${tx.direction === 'in' ? '#4ade80' : '#f87171'};">
                                    <div class="d-flex justify-content-between align-items-start">
                                        <div>
                                            <span class="badge ${tx.direction === 'in' ? 'bg-success' : 'bg-danger'}" style="font-size: 0.65rem; margin-right: 6px;">
                                                ${tx.direction === 'in' ? 'IN' : 'OUT'}
                                            </span>
                                            <strong style="color: #667eea; font-size: 0.95rem;">
                                                ${formatTokenAmount(tx.value)} ${tx.token_symbol}
                                            </strong>
                                        </div>
                                        ${tx.timestamp ? `<small style="color: #666;">${tx.timestamp}</small>` : ''}
                                    </div>
                                    <div style="margin-top: 4px;">
                                        <div style="color: #9d9dff; font-weight: 500; font-size: 0.85rem;">
                                            ${tx.token_name || 'Unknown Token'}
                                        </div>
                                    </div>
                                    <div class="d-flex justify-content-between mt-1" style="font-size: 0.75rem;">
                                        <span style="color: #666;">
                                            ${tx.direction === 'in' ? 'From: ' : 'To: '}
                                            <span style="font-family: monospace; color: #888;">
                                                ${tx.direction === 'in' ? shortenAddress(tx.from) : shortenAddress(tx.to)}
                                            </span>
                                        </span>
                                        <span class="hash" style="cursor: pointer; color: #667eea;" onclick="copyToClipboard('${tx.hash}')" title="Click to copy TX hash">
                                            ${tx.hash ? tx.hash.slice(0, 10) + '...' : ''}
                                        </span>
                                    </div>
                                    ${tx.contract_address ? `
                                    <div style="font-size: 0.7rem; color: #555; margin-top: 2px;">
                                        Contract: <span style="font-family: monospace;">${shortenAddress(tx.contract_address)}</span>
                                    </div>
                                    ` : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }

        // MEV Exposure
        if (mev && !mev.error && (mev.sandwich_attacks || mev.total_mev_loss || mev.mev_transactions)) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-exclamation-triangle"></i> MEV Exposure</h6>
                    ${mev.sandwich_attacks !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Sandwich Attacks</span>
                        <span class="detail-value" style="color: #f87171;">${mev.sandwich_attacks}</span>
                    </div>
                    ` : ''}
                    ${mev.total_mev_loss !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Total MEV Loss</span>
                        <span class="detail-value" style="color: #f87171;">${mev.total_mev_loss.toFixed(4)} ETH</span>
                    </div>
                    ` : ''}
                    ${mev.frontrun_count !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Frontrun Count</span>
                        <span class="detail-value">${mev.frontrun_count}</span>
                    </div>
                    ` : ''}
                    ${mev.mev_bot_interactions !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">MEV Bot Interactions</span>
                        <span class="detail-value">${mev.mev_bot_interactions}</span>
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Whale Tracker
        if (whale && !whale.error && (whale.is_whale || whale.whale_transactions || whale.total_whale_volume)) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-water"></i> Whale Activity</h6>
                    <div class="detail-row">
                        <span class="detail-label">Is Whale</span>
                        <span class="detail-value">${whale.is_whale ? '<span style="color: #4ade80;">Yes</span>' : 'No'}</span>
                    </div>
                    ${whale.whale_transactions !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Whale Transactions</span>
                        <span class="detail-value">${whale.whale_transactions}</span>
                    </div>
                    ` : ''}
                    ${whale.total_whale_volume !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Total Whale Volume</span>
                        <span class="detail-value">${whale.total_whale_volume.toFixed(2)} ETH</span>
                    </div>
                    ` : ''}
                    ${whale.largest_tx !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Largest Transaction</span>
                        <span class="detail-value">${whale.largest_tx.toFixed(4)} ETH</span>
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Flash Loans
        if (flashLoans && !flashLoans.error && (flashLoans.flash_loan_count || flashLoans.total_flash_loans)) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-lightning-fill"></i> Flash Loans</h6>
                    <div class="detail-row">
                        <span class="detail-label">Flash Loan Count</span>
                        <span class="detail-value">${flashLoans.flash_loan_count || flashLoans.total_flash_loans || 0}</span>
                    </div>
                    ${flashLoans.total_volume !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Total Volume</span>
                        <span class="detail-value">${flashLoans.total_volume.toFixed(2)} ETH</span>
                    </div>
                    ` : ''}
                    ${flashLoans.arbitrage_detected ? `
                    <div class="detail-row">
                        <span class="detail-label">Arbitrage Detected</span>
                        <span class="detail-value" style="color: #fbbf24;">Yes</span>
                    </div>
                    ` : ''}
                    ${flashLoans.providers && flashLoans.providers.length > 0 ? `
                    <div class="mt-2">
                        <small class="text-muted">Providers:</small><br>
                        ${flashLoans.providers.map(p => `<span class="token-badge">${p}</span>`).join('')}
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Sniper Detection
        if (sniper && !sniper.error && (sniper.is_sniper || sniper.sniper_score || sniper.early_buys)) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-crosshair"></i> Sniper Detection</h6>
                    <div class="detail-row">
                        <span class="detail-label">Is Sniper</span>
                        <span class="detail-value">${sniper.is_sniper ? '<span style="color: #f87171;">Yes</span>' : 'No'}</span>
                    </div>
                    ${sniper.sniper_score !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Sniper Score</span>
                        <span class="detail-value">${sniper.sniper_score}/100</span>
                    </div>
                    ` : ''}
                    ${sniper.early_buys !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Early Buys</span>
                        <span class="detail-value">${sniper.early_buys}</span>
                    </div>
                    ` : ''}
                    ${sniper.avg_buy_block !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Avg Buy Block</span>
                        <span class="detail-value">${sniper.avg_buy_block}</span>
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Copy Trading
        if (copyTrading && !copyTrading.error && (copyTrading.copy_score || copyTrading.performance)) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-people-fill"></i> Copy Trading Analysis</h6>
                    ${copyTrading.copy_score !== undefined ? `
                    <div class="text-center mb-3">
                        <div style="font-size: 1.5rem; font-weight: bold; color: ${copyTrading.copy_score >= 70 ? '#4ade80' : copyTrading.copy_score >= 40 ? '#fbbf24' : '#f87171'};">
                            ${copyTrading.copy_score}/100
                        </div>
                        <small class="text-muted">Copy Score</small>
                    </div>
                    ` : ''}
                    ${copyTrading.win_rate !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Win Rate</span>
                        <span class="detail-value">${(copyTrading.win_rate * 100).toFixed(1)}%</span>
                    </div>
                    ` : ''}
                    ${copyTrading.avg_return !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Avg Return</span>
                        <span class="detail-value" style="color: ${copyTrading.avg_return >= 0 ? '#4ade80' : '#f87171'};">
                            ${copyTrading.avg_return >= 0 ? '+' : ''}${(copyTrading.avg_return * 100).toFixed(1)}%
                        </span>
                    </div>
                    ` : ''}
                    ${copyTrading.recommendation ? `
                    <div class="mt-2">
                        <span class="badge ${copyTrading.recommendation === 'Strong Copy' ? 'bg-success' : copyTrading.recommendation === 'Copy' ? 'bg-info' : 'bg-secondary'}">
                            ${copyTrading.recommendation}
                        </span>
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Funding Flow
        if (fundingFlow && !fundingFlow.error && (fundingFlow.sources || fundingFlow.destinations || fundingFlow.suspicious_patterns)) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-arrow-left-right"></i> Funding Flow</h6>
                    ${fundingFlow.total_inflow !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label direction-in">Total Inflow</span>
                        <span class="detail-value">${fundingFlow.total_inflow.toFixed(4)} ETH</span>
                    </div>
                    ` : ''}
                    ${fundingFlow.total_outflow !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label direction-out">Total Outflow</span>
                        <span class="detail-value">${fundingFlow.total_outflow.toFixed(4)} ETH</span>
                    </div>
                    ` : ''}
                    ${fundingFlow.unique_sources !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Unique Sources</span>
                        <span class="detail-value">${fundingFlow.unique_sources}</span>
                    </div>
                    ` : ''}
                    ${fundingFlow.suspicious_patterns && fundingFlow.suspicious_patterns.length > 0 ? `
                    <div class="mt-2">
                        <small class="text-muted" style="color: #f87171;">Suspicious Patterns:</small><br>
                        ${fundingFlow.suspicious_patterns.map(p => `<span class="token-badge" style="background: #4a1a1a; color: #f87171;">${p}</span>`).join('')}
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Liquidity Pools
        if (liquidity && !liquidity.error && (liquidity.lp_positions || liquidity.total_lp_value)) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-droplet-fill"></i> Liquidity Positions</h6>
                    ${liquidity.total_lp_value !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Total LP Value</span>
                        <span class="detail-value">$${liquidity.total_lp_value.toLocaleString()}</span>
                    </div>
                    ` : ''}
                    ${liquidity.active_pools !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Active Pools</span>
                        <span class="detail-value">${liquidity.active_pools}</span>
                    </div>
                    ` : ''}
                    ${liquidity.lp_positions && liquidity.lp_positions.length > 0 ? `
                    <div class="mt-2">
                        <small class="text-muted">Top Pools:</small><br>
                        ${liquidity.lp_positions.slice(0, 3).map(lp => `
                            <span class="token-badge">${lp.pair || lp.pool}: ${lp.value ? '$' + lp.value.toLocaleString() : ''}</span>
                        `).join('')}
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Governance
        if (governance && !governance.error && (governance.governance_score || governance.votes_cast || governance.proposals_voted)) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-bank"></i> Governance Participation</h6>
                    ${governance.governance_score !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Governance Score</span>
                        <span class="detail-value">${governance.governance_score}/100</span>
                    </div>
                    ` : ''}
                    ${governance.votes_cast !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Votes Cast</span>
                        <span class="detail-value">${governance.votes_cast}</span>
                    </div>
                    ` : ''}
                    ${governance.proposals_voted !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Proposals Voted</span>
                        <span class="detail-value">${governance.proposals_voted}</span>
                    </div>
                    ` : ''}
                    ${governance.governance_tokens && governance.governance_tokens.length > 0 ? `
                    <div class="mt-2">
                        <small class="text-muted">Governance Tokens:</small><br>
                        ${governance.governance_tokens.map(t => `<span class="token-badge">${t}</span>`).join('')}
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Token Approvals
        if (approvals && !approvals.error && (approvals.approvals || approvals.high_risk_approvals)) {
            const approvalsList = approvals.approvals || [];
            const highRisk = approvals.high_risk_approvals || approvalsList.filter(a => a.risk === 'high').length;
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-shield-check"></i> Token Approvals</h6>
                    <div class="detail-row">
                        <span class="detail-label">Total Approvals</span>
                        <span class="detail-value">${approvalsList.length}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">High Risk</span>
                        <span class="detail-value" style="color: ${highRisk > 0 ? '#f87171' : '#4ade80'};">${highRisk}</span>
                    </div>
                    ${approvals.unlimited_approvals !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Unlimited Approvals</span>
                        <span class="detail-value" style="color: ${approvals.unlimited_approvals > 0 ? '#fbbf24' : '#4ade80'};">
                            ${approvals.unlimited_approvals}
                        </span>
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Address Clustering
        if (clustering && !clustering.error && (clustering.related_addresses || clustering.cluster_size)) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-diagram-2"></i> Address Clustering</h6>
                    ${clustering.cluster_size !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Cluster Size</span>
                        <span class="detail-value">${clustering.cluster_size}</span>
                    </div>
                    ` : ''}
                    ${clustering.sybil_score !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Sybil Score</span>
                        <span class="detail-value" style="color: ${clustering.sybil_score > 50 ? '#f87171' : '#4ade80'};">
                            ${clustering.sybil_score}/100
                        </span>
                    </div>
                    ` : ''}
                    ${clustering.related_addresses && clustering.related_addresses.length > 0 ? `
                    <div class="mt-2">
                        <small class="text-muted">Related Addresses:</small><br>
                        ${clustering.related_addresses.slice(0, 3).map(a => `
                            <span class="token-badge" style="font-family: monospace; font-size: 0.7rem;">${shortenAddress(a.address || a)}</span>
                        `).join('')}
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Smart Money
        if (smartMoney && !smartMoney.error && (smartMoney.smart_money_interactions || smartMoney.following_smart_money)) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-lightbulb-fill"></i> Smart Money</h6>
                    ${smartMoney.is_smart_money !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Is Smart Money</span>
                        <span class="detail-value">${smartMoney.is_smart_money ? '<span style="color: #4ade80;">Yes</span>' : 'No'}</span>
                    </div>
                    ` : ''}
                    ${smartMoney.smart_money_interactions !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">SM Interactions</span>
                        <span class="detail-value">${smartMoney.smart_money_interactions}</span>
                    </div>
                    ` : ''}
                    ${smartMoney.following_count !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Following SM Wallets</span>
                        <span class="detail-value">${smartMoney.following_count}</span>
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Airdrops
        if (airdrops && !airdrops.error && (airdrops.claimed_airdrops || airdrops.eligible_airdrops || airdrops.total_value)) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-gift-fill"></i> Airdrops</h6>
                    ${airdrops.claimed_airdrops !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Claimed Airdrops</span>
                        <span class="detail-value">${airdrops.claimed_airdrops}</span>
                    </div>
                    ` : ''}
                    ${airdrops.total_value !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Total Value</span>
                        <span class="detail-value" style="color: #4ade80;">$${airdrops.total_value.toLocaleString()}</span>
                    </div>
                    ` : ''}
                    ${airdrops.eligible_airdrops && airdrops.eligible_airdrops.length > 0 ? `
                    <div class="mt-2">
                        <small class="text-muted">Eligible:</small><br>
                        ${airdrops.eligible_airdrops.slice(0, 5).map(a => `<span class="token-badge">${a.name || a}</span>`).join('')}
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Gas Optimizer
        if (gasOptimizer && !gasOptimizer.error && (gasOptimizer.total_gas_spent || gasOptimizer.avg_gas_price)) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-fuel-pump"></i> Gas Analysis</h6>
                    ${gasOptimizer.total_gas_spent !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Total Gas Spent</span>
                        <span class="detail-value">${gasOptimizer.total_gas_spent.toFixed(4)} ETH</span>
                    </div>
                    ` : ''}
                    ${gasOptimizer.avg_gas_price !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Avg Gas Price</span>
                        <span class="detail-value">${gasOptimizer.avg_gas_price.toFixed(1)} Gwei</span>
                    </div>
                    ` : ''}
                    ${gasOptimizer.optimal_time ? `
                    <div class="detail-row">
                        <span class="detail-label">Optimal TX Time</span>
                        <span class="detail-value">${gasOptimizer.optimal_time}</span>
                    </div>
                    ` : ''}
                    ${gasOptimizer.savings_potential !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">Potential Savings</span>
                        <span class="detail-value" style="color: #4ade80;">${gasOptimizer.savings_potential.toFixed(4)} ETH</span>
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // ENS
        if (ens && !ens.error && (ens.ens_names || ens.primary_name)) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-tag-fill"></i> ENS Names</h6>
                    ${ens.primary_name ? `
                    <div class="detail-row">
                        <span class="detail-label">Primary Name</span>
                        <span class="detail-value" style="color: #667eea;">${ens.primary_name}</span>
                    </div>
                    ` : ''}
                    ${ens.ens_names && ens.ens_names.length > 0 ? `
                    <div class="mt-2">
                        <small class="text-muted">Owned Names:</small><br>
                        ${ens.ens_names.slice(0, 5).map(name => `<span class="token-badge">${name}</span>`).join('')}
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Security Scan (for contracts)
        if (security && !security.error && (security.is_contract || security.risk_level)) {
            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-shield-exclamation"></i> Security Scan</h6>
                    <div class="detail-row">
                        <span class="detail-label">Is Contract</span>
                        <span class="detail-value">${security.is_contract ? 'Yes' : 'No'}</span>
                    </div>
                    ${security.risk_level ? `
                    <div class="detail-row">
                        <span class="detail-label">Risk Level</span>
                        <span class="detail-value" style="color: ${security.risk_level === 'high' ? '#f87171' : security.risk_level === 'medium' ? '#fbbf24' : '#4ade80'};">
                            ${security.risk_level.toUpperCase()}
                        </span>
                    </div>
                    ` : ''}
                    ${security.issues && security.issues.length > 0 ? `
                    <div class="mt-2">
                        <small class="text-muted" style="color: #f87171;">Issues Found:</small><br>
                        ${security.issues.slice(0, 3).map(i => `<span class="token-badge" style="background: #4a1a1a; color: #f87171;">${i}</span>`).join('')}
                    </div>
                    ` : ''}
                </div>
            `;
        }

        // Graph connections summary
        if (graphData && graphData.nodes) {
            const incomingLinks = graphData.links ? graphData.links.filter(l => l.direction === 'in').length : 0;
            const outgoingLinks = graphData.links ? graphData.links.filter(l => l.direction === 'out').length : 0;
            const tokenTransfers = graphData.links ? graphData.links.filter(l => l.type === 'token_transfer').length : 0;

            html += `
                <div class="detail-card">
                    <h6><i class="bi bi-diagram-3"></i> Connection Summary</h6>
                    <div class="detail-row">
                        <span class="detail-label">Connected Addresses</span>
                        <span class="detail-value">${graphData.nodes.length - 1}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label direction-in">Incoming TXs</span>
                        <span class="detail-value">${incomingLinks}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label direction-out">Outgoing TXs</span>
                        <span class="detail-value">${outgoingLinks}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Token Transfers</span>
                        <span class="detail-value">${tokenTransfers}</span>
                    </div>
                </div>
            `;

            // Top connections
            if (graphData.nodes.length > 1) {
                const otherNodes = graphData.nodes.filter(n => n.id.toLowerCase() !== address.toLowerCase()).slice(0, 5);
                html += `
                    <div class="detail-card">
                        <h6><i class="bi bi-people"></i> Top Connections</h6>
                        <div class="tx-list">
                            ${otherNodes.map(n => `
                                <div class="tx-item" style="cursor: pointer;" onclick="closeDetailsModal(); setTimeout(() => openDetailsModal('${n.id}'), 300);">
                                    <div class="hash">${shortenAddress(n.id)}</div>
                                    <div class="d-flex justify-content-between">
                                        ${n.tx_count ? `<small class="text-muted">${n.tx_count} txs</small>` : ''}
                                        ${n.value ? `<small class="value">${n.value.toFixed(4)} ETH</small>` : ''}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
        }

        // Action buttons
        html += `
            <div class="modal-btn-group">
                <button class="modal-btn modal-btn-primary" onclick="window.open('/address/${chain}/${address}', '_blank')">
                    <i class="bi bi-box-arrow-up-right"></i> Full Page
                </button>
                <button class="modal-btn modal-btn-secondary" onclick="window.open('/analytics?address=${address}&chain=${chain}', '_blank')">
                    <i class="bi bi-graph-up"></i> Analytics
                </button>
                <button class="modal-btn modal-btn-secondary" onclick="window.open('/advanced?address=${address}&chain=${chain}', '_blank')">
                    <i class="bi bi-gear"></i> Advanced
                </button>
            </div>
            <div class="modal-btn-group mt-2">
                <button class="modal-btn modal-btn-secondary" onclick="window.open('https://etherscan.io/address/${address}', '_blank')">
                    <i class="bi bi-globe"></i> Etherscan
                </button>
            </div>
        `;

        modalBody.innerHTML = html;
    })
    .catch(error => {
        modalBody.innerHTML = `
            <div class="text-center py-4 text-danger">
                <i class="bi bi-exclamation-triangle" style="font-size: 2rem;"></i>
                <p class="mt-2">Failed to load details: ${error.message}</p>
            </div>
        `;
    });
}

function closeDetailsModal() {
    const overlay = document.getElementById('graph-modal-overlay');
    if (overlay) {
        overlay.classList.remove('show');
    }
}

function expandNode(address) {
    const existingNodeIds = graphState.nodes.map(n => n.id.toLowerCase());

    // Show loading indicator on the node
    graphState.g.selectAll('.node')
        .filter(d => d.id.toLowerCase() === address.toLowerCase())
        .select('circle')
        .attr('stroke', '#17a2b8')
        .attr('stroke-width', 4)
        .attr('stroke-dasharray', '5,5');

    // Also update expand indicator
    graphState.g.selectAll('.node')
        .filter(d => d.id.toLowerCase() === address.toLowerCase())
        .select('.expand-indicator')
        .text('...');

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
            alert('Error expanding node: ' + data.error);
            return;
        }

        // Mark node as expanded
        graphState.expandedNodes.add(address.toLowerCase());

        // Get position of expanded node for new node placement
        const expandedNode = graphState.nodes.find(n => n.id.toLowerCase() === address.toLowerCase());
        const baseX = expandedNode ? expandedNode.x : graphState.width / 2;
        const baseY = expandedNode ? expandedNode.y : graphState.height / 2;

        // Add new nodes
        let newNodesCount = 0;
        if (data.nodes && data.nodes.length > 0) {
            data.nodes.forEach((node, i) => {
                // Check if node already exists
                if (!graphState.nodes.some(n => n.id.toLowerCase() === node.id.toLowerCase())) {
                    const angle = (2 * Math.PI * i) / data.nodes.length;
                    node.x = baseX + Math.cos(angle) * 120;
                    node.y = baseY + Math.sin(angle) * 120;
                    graphState.nodes.push(node);
                    newNodesCount++;
                }
            });
        }

        // Add new links
        let newLinksCount = 0;
        if (data.links && data.links.length > 0) {
            data.links.forEach(link => {
                // Check if link already exists
                const exists = graphState.links.some(l => {
                    const lSource = (l.source.id || l.source).toLowerCase();
                    const lTarget = (l.target.id || l.target).toLowerCase();
                    return lSource === link.source.toLowerCase() && lTarget === link.target.toLowerCase();
                });
                if (!exists) {
                    graphState.links.push(link);
                    newLinksCount++;
                }
            });
        }

        console.log(`Expanded ${address}: +${newNodesCount} nodes, +${newLinksCount} links`);

        // Restart simulation with new data
        graphState.simulation.nodes(graphState.nodes);
        graphState.simulation.force('link').links(graphState.links);
        graphState.simulation.alpha(0.5).restart();

        // Re-render
        renderGraph();

        // Update selected node info if it was the expanded node
        if (graphState.selectedNode && graphState.selectedNode.id.toLowerCase() === address.toLowerCase()) {
            showNodeInfo(graphState.selectedNode);
        }
    })
    .catch(error => {
        console.error('Failed to expand node:', error);
        alert('Failed to expand node: ' + error.message);
    });
}

function expandAllVisible() {
    const unexpandedNodes = graphState.nodes.filter(n => !graphState.expandedNodes.has(n.id.toLowerCase()));

    if (unexpandedNodes.length === 0) {
        alert('All visible nodes are already expanded');
        return;
    }

    if (unexpandedNodes.length > 5) {
        if (!confirm(`This will expand ${unexpandedNodes.length} nodes. This may take a while. Continue?`)) {
            return;
        }
    }

    // Expand nodes sequentially
    let index = 0;
    function expandNext() {
        if (index < unexpandedNodes.length) {
            expandNode(unexpandedNodes[index].id);
            index++;
            setTimeout(expandNext, 1000); // Wait 1 second between expansions
        }
    }
    expandNext();
}

function updateCounts() {
    const nodeCount = document.getElementById('node-count');
    const linkCount = document.getElementById('link-count');
    if (nodeCount) nodeCount.textContent = graphState.nodes.length;
    if (linkCount) linkCount.textContent = graphState.links.length;
}

function resetGraph() {
    window.location.reload();
}

function centerGraph() {
    graphState.svg.transition()
        .duration(500)
        .call(graphState.zoom.transform, d3.zoomIdentity.translate(0, 0).scale(1));
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show brief notification
        const toast = document.createElement('div');
        toast.className = 'position-fixed bottom-0 end-0 p-3';
        toast.style.zIndex = '10000';
        toast.innerHTML = `
            <div class="toast show bg-success text-white">
                <div class="toast-body">
                    <i class="bi bi-check-circle"></i> Address copied!
                </div>
            </div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
    });
}

function addLegend() {
    const legend = graphState.svg.append('g')
        .attr('class', 'legend')
        .attr('transform', 'translate(20, 20)');

    const legendData = [
        { label: 'Central', color: '#0d6efd' },
        { label: 'Expanded', color: '#17a2b8', stroke: '#17a2b8' },
        { label: 'Click + to expand', color: '#6c757d' },
        { label: 'Outgoing', color: '#dc3545', line: true },
        { label: 'Incoming', color: '#28a745', line: true },
        { label: 'Token', color: '#6c757d', line: true, dashed: true }
    ];

    legendData.forEach((item, i) => {
        const g = legend.append('g')
            .attr('transform', `translate(0, ${i * 18})`);

        if (item.line) {
            g.append('line')
                .attr('x1', 0)
                .attr('y1', 8)
                .attr('x2', 18)
                .attr('y2', 8)
                .attr('stroke', item.color)
                .attr('stroke-width', 2)
                .attr('stroke-dasharray', item.dashed ? '4,4' : null);
        } else {
            g.append('circle')
                .attr('cx', 9)
                .attr('cy', 8)
                .attr('r', 7)
                .attr('fill', item.color)
                .attr('stroke', item.stroke || '#fff')
                .attr('stroke-width', item.stroke ? 2 : 1);
        }

        g.append('text')
            .attr('x', 26)
            .attr('y', 12)
            .attr('font-size', '10px')
            .attr('fill', '#666')
            .text(item.label);
    });
}

function getNodeColor(d) {
    if (d.is_central) return '#0d6efd';
    if (graphState.expandedNodes.has(d.id.toLowerCase())) return '#17a2b8';
    return '#6c757d';
}

function formatTokenAmount(amount) {
    if (amount === 0 || amount === undefined || amount === null) return '0';
    if (Math.abs(amount) >= 1000000000) {
        return (amount / 1000000000).toFixed(2) + 'B';
    } else if (Math.abs(amount) >= 1000000) {
        return (amount / 1000000).toFixed(2) + 'M';
    } else if (Math.abs(amount) >= 1000) {
        return (amount / 1000).toFixed(2) + 'K';
    } else if (Math.abs(amount) >= 1) {
        return amount.toFixed(4);
    } else if (Math.abs(amount) >= 0.0001) {
        return amount.toFixed(6);
    } else {
        return amount.toExponential(2);
    }
}

function shortenAddress(address) {
    if (address && address.length > 10) {
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    }
    return address || '';
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

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeDetailsModal();
    }
});
