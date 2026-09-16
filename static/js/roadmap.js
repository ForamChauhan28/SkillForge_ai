/* ═══════════════════════════════════════════════════
   SkillForge AI — Roadmap Visualization (vis-network)
   ═══════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {
    if (typeof ROADMAP_DATA === 'undefined' || !ROADMAP_DATA) return;
    initRoadmap();
});


function initRoadmap() {
    var container = document.getElementById('roadmapGraph');
    if (!container) return;

    var roadmap = ROADMAP_DATA.roadmap || ROADMAP_DATA;
    var phases = roadmap.phases || [];
    var dbNodes = ROADMAP_NODES_DB || [];
    var isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    // Color palette
    var colors = {
        goal: { bg: '#c9a84c', border: '#b8973b', font: '#ffffff' },
        phase: { bg: isDark ? '#7c6df0' : '#4a3f8a', border: isDark ? '#5b4fb5' : '#3a2f7a', font: '#ffffff' },
        phaseComplete: { bg: isDark ? '#00b894' : '#2d8659', border: isDark ? '#00916f' : '#1a6b42', font: '#ffffff' },
        topic: { bg: isDark ? '#2a2a3e' : '#ede7db', border: isDark ? '#3a3a52' : '#ccc5b8', font: isDark ? '#d0d0e0' : '#1a1a2e' },
        topicComplete: { bg: isDark ? '#00b894' : '#2d8659', border: isDark ? '#00916f' : '#1a6b42', font: '#ffffff' },
        edgeDefault: isDark ? '#555580' : '#bbb5a8',
        edgeActive: isDark ? '#7c6df0' : '#4a3f8a',
        edgeComplete: isDark ? '#00b894' : '#2d8659'
    };

    var visNodes = [];
    var visEdges = [];

    // Central goal node
    visNodes.push({
        id: 'goal',
        label: roadmap.goal || 'Your Goal',
        shape: 'box',
        color: { background: colors.goal.bg, border: colors.goal.border,
                 highlight: { background: '#dbb85e', border: colors.goal.border } },
        font: { color: colors.goal.font, size: 16, face: 'Inter', bold: { color: colors.goal.font } },
        borderWidth: 2,
        margin: { top: 14, bottom: 14, left: 20, right: 20 },
        shadow: { enabled: true, size: 10, color: 'rgba(201,168,76,0.3)' }
    });

    var prevPhaseId = 'goal';

    phases.forEach(function (phase, phaseIdx) {
        var pid = phase.phase_id || (phaseIdx + 1);
        var phaseNodeId = 'phase_' + pid;
        var phaseTopics = phase.topics || [];

        // Find matching DB nodes for this phase
        var phaseDbNodes = dbNodes.filter(function (n) { return n.phase_id === pid; });
        var completedCount = phaseDbNodes.filter(function (n) { return n.is_completed; }).length;
        var isPhaseComplete = phaseDbNodes.length > 0 && completedCount === phaseDbNodes.length;

        var phaseColor = isPhaseComplete ? colors.phaseComplete : colors.phase;

        // Phase node
        visNodes.push({
            id: phaseNodeId,
            label: (phase.title || ('Phase ' + (phaseIdx + 1))) +
                   '\n(' + completedCount + '/' + phaseDbNodes.length + ')',
            shape: 'box',
            color: { background: phaseColor.bg, border: phaseColor.border,
                     highlight: { background: phaseColor.bg, border: phaseColor.border } },
            font: { color: phaseColor.font, size: 13, face: 'Inter', multi: true,
                    bold: { color: phaseColor.font } },
            borderWidth: 2,
            margin: { top: 12, bottom: 12, left: 16, right: 16 },
            shadow: { enabled: true, size: 8, color: 'rgba(0,0,0,0.15)' }
        });

        // Edge from previous phase
        visEdges.push({
            from: prevPhaseId,
            to: phaseNodeId,
            arrows: { to: { enabled: true, scaleFactor: 0.8 } },
            color: { color: isPhaseComplete ? colors.edgeComplete : colors.edgeActive, opacity: 0.8 },
            width: 2.5,
            smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.4 }
        });

        // Topic nodes
        phaseTopics.forEach(function (topic, topicIdx) {
            var topicNodeId = 'topic_' + pid + '_' + topicIdx;
            var topicName = (typeof topic === 'string') ? topic : (topic.name || String(topic));
            var dbNode = null;

            // Match topic to DB node
            for (var i = 0; i < phaseDbNodes.length; i++) {
                if (phaseDbNodes[i].topic_name === topicName) {
                    dbNode = phaseDbNodes[i];
                    break;
                }
            }

            var isCompleted = dbNode ? dbNode.is_completed : false;
            var topicColor = isCompleted ? colors.topicComplete : colors.topic;

            visNodes.push({
                id: topicNodeId,
                label: topicName,
                shape: 'box',
                color: { background: topicColor.bg, border: topicColor.border,
                         highlight: { background: topicColor.bg, border: topicColor.border } },
                font: { color: topicColor.font, size: 11, face: 'Inter' },
                borderWidth: 1,
                margin: { top: 8, bottom: 8, left: 12, right: 12 },
                shadow: false,
                // Custom data
                _topicData: (typeof topic === 'object') ? topic : { name: topic },
                _dbNodeId: dbNode ? dbNode.node_id : null,
                _isCompleted: isCompleted
            });

            visEdges.push({
                from: phaseNodeId,
                to: topicNodeId,
                color: { color: isCompleted ? colors.edgeComplete : colors.edgeDefault, opacity: 0.5 },
                width: 1,
                smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.3 }
            });
        });

        prevPhaseId = phaseNodeId;
    });

    // vis-network options
    var options = {
        layout: {
            hierarchical: {
                direction: 'UD',
                sortMethod: 'directed',
                levelSeparation: 130,
                nodeSpacing: 170,
                treeSpacing: 220,
                blockShifting: true,
                edgeMinimization: true
            }
        },
        physics: false,
        interaction: {
            hover: true,
            navigationButtons: true,
            keyboard: { enabled: true },
            zoomView: true,
            dragView: true,
            tooltipDelay: 200
        },
        nodes: {
            borderWidthSelected: 3,
            chosen: true
        },
        edges: {
            chosen: false
        }
    };

    var data = {
        nodes: new vis.DataSet(visNodes),
        edges: new vis.DataSet(visEdges)
    };

    var network = new vis.Network(container, data, options);

    // Click handler
    network.on('click', function (params) {
        if (params.nodes.length > 0) {
            var clickedId = params.nodes[0];
            if (clickedId.indexOf('topic_') === 0) {
                var node = data.nodes.get(clickedId);
                if (node) {
                    showNodeDetail(node);
                }
            }
        } else {
            closeNodeDetail();
        }
    });

    // Fit view after render
    network.once('afterDrawing', function () {
        network.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
    });
}


function showNodeDetail(node) {
    var panel = document.getElementById('nodeDetailPanel');
    if (!panel) return;

    var topicData = node._topicData || {};
    var isCompleted = node._isCompleted || false;
    var dbNodeId = node._dbNodeId;
    var topicName = topicData.name || node.label || 'Topic';

    var html = '<button class="close-btn" onclick="closeNodeDetail()">✕</button>';
    html += '<h3 style="margin-bottom: 1rem; padding-right: 2rem;">' + topicName + '</h3>';

    // Status badge
    if (isCompleted) {
        html += '<span class="badge badge-success" style="margin-bottom: 1rem;">✅ Completed</span>';
    } else {
        html += '<span class="badge badge-primary" style="margin-bottom: 1rem;">📖 In Progress</span>';
    }

    // Description
    if (topicData.description) {
        html += '<p style="margin-bottom: 1rem; font-size: 0.9rem; color: var(--text-secondary);">' + topicData.description + '</p>';
    }

    // Priority
    if (topicData.priority) {
        var prClass = topicData.priority === 'high' ? 'danger' : (topicData.priority === 'medium' ? 'warning' : 'success');
        html += '<div style="margin-bottom: 1rem;"><span class="badge badge-' + prClass + '">⚡ ' + topicData.priority.charAt(0).toUpperCase() + topicData.priority.slice(1) + ' Priority</span></div>';
    }

    // Resources
    if (topicData.resources && topicData.resources.length > 0) {
        html += '<h4 style="margin: 1rem 0 0.5rem; font-size: 0.95rem; color: var(--text-primary);">📚 Resources</h4>';
        html += '<ul class="resource-list">';
        topicData.resources.forEach(function (r) {
            html += '<li>' + r + '</li>';
        });
        html += '</ul>';
    }

    html += '<div class="divider"></div>';

    // Toggle button
    if (dbNodeId) {
        if (isCompleted) {
            html += '<button class="btn btn-secondary w-full" onclick="toggleNodeCompletion(' + dbNodeId + ', false)">';
            html += '↩️ Mark Incomplete</button>';
        } else {
            html += '<button class="btn btn-success w-full" onclick="toggleNodeCompletion(' + dbNodeId + ', true)">';
            html += '✅ Mark Complete</button>';
        }
    }

    html += '<p style="margin-top: 1rem; font-size: 0.8rem; color: var(--text-tertiary); text-align: center;">';
    html += isCompleted ? '🎉 Great job! Keep going!' : '📖 Keep learning, you\'ve got this!';
    html += '</p>';

    panel.innerHTML = html;
    panel.classList.add('open');
}


function closeNodeDetail() {
    var panel = document.getElementById('nodeDetailPanel');
    if (panel) panel.classList.remove('open');
}


function toggleNodeCompletion(nodeId, markComplete) {
    apiPost('/api/toggle-node/' + nodeId, {})
        .then(function (response) {
            if (response.success) {
                showToast(markComplete ? 'Topic marked as complete! 🎉' : 'Topic marked as incomplete', 'success');
                setTimeout(function () { location.reload(); }, 600);
            }
        })
        .catch(function (error) {
            showToast('Failed to update: ' + error.message, 'danger');
        });
}
