(() => {
    const plotElement = document.getElementById("hemolysis-plot");
    if (!plotElement || !window.hemolysisPlotData) {
        return;
    }

    const uploadId = plotElement.dataset.uploadId;
    const alphaInput = document.querySelector('input[name="alpha"]');
    const statusElement = document.getElementById("recalculate-status");
    let plotData = window.hemolysisPlotData;
    let excludedPointIds = new Set(plotData.excluded_point_ids || []);
    let committedExcludedPointIds = new Set(excludedPointIds);
    let requestNumber = 0;

    function rgba(hex, alpha) {
        const red = parseInt(hex.slice(1, 3), 16);
        const green = parseInt(hex.slice(3, 5), 16);
        const blue = parseInt(hex.slice(5, 7), 16);
        return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
    }

    function createTraces(data) {
        const traces = [];
        data.groups.forEach((group, groupIndex) => {
            const axisNumber = groupIndex + 1;
            const xaxis = axisNumber === 1 ? "x" : `x${axisNumber}`;
            const yaxis = axisNumber === 1 ? "y" : `y${axisNumber}`;

            data.individuals
                .filter((individual) => individual.group === group.name)
                .forEach((individual) => {
                    traces.push({
                        type: "scatter",
                        mode: "lines+markers",
                        x: individual.x,
                        y: individual.y,
                        xaxis,
                        yaxis,
                        meta: { type: "measurement", point_ids: individual.point_ids },
                        customdata: individual.point_ids.map((pointId, index) => [
                            pointId,
                            individual.value_text[index],
                        ]),
                        line: { color: rgba(group.color, 0.35), width: 1 },
                        marker: {
                            color: individual.point_ids.map((pointId) =>
                                excludedPointIds.has(pointId) ? "#c9cdd1" : group.color
                            ),
                            size: 7,
                            line: { color: "white", width: 0.5 },
                        },
                        hovertemplate: "Hemolysis: %{customdata[1]}%<extra></extra>",
                        showlegend: false,
                    });
                });

            const means = data.means.find((entry) => entry.group === group.name);
            if (means) {
                traces.push({
                    type: "scatter",
                    mode: "lines+markers",
                    x: means.x,
                    y: means.mean,
                    xaxis,
                    yaxis,
                    line: { color: group.color, width: 3 },
                    marker: {
                        color: group.color,
                        size: 9,
                        line: { color: "white", width: 1.5 },
                    },
                    error_y: {
                        type: "data",
                        array: means.sem.map((value) => value === null ? 0 : value),
                        visible: true,
                        thickness: 1.5,
                        width: 4,
                    },
                    hoverinfo: "skip",
                    showlegend: false,
                });
            }
        });
        return traces;
    }

    function createLayout(data) {
        const groupCount = data.groups.length;
        const gap = 0.08;
        const panelWidth = (1 - gap * (groupCount - 1)) / groupCount;
        const decisionCount = data.decisions.length;
        const layout = {
            title: {
                text: "Hemolysis % over time by group (thin = individual, thick = mean ± SEM)",
                font: { size: 16 },
            },
            height: 560 + decisionCount * 28,
            margin: { t: 105, r: 25, b: 105 + decisionCount * 24, l: 70 },
            hovermode: "closest",
            showlegend: false,
            annotations: [],
        };

        data.groups.forEach((group, index) => {
            const axisNumber = index + 1;
            const axisName = axisNumber === 1 ? "" : axisNumber;
            const xaxisKey = `xaxis${axisName}`;
            const yaxisKey = `yaxis${axisName}`;
            const start = index * (panelWidth + gap);
            const end = start + panelWidth;
            const xaxis = {
                domain: [start, end],
                anchor: axisNumber === 1 ? "y" : `y${axisNumber}`,
                title: { text: "Time (days)" },
                tickmode: "array",
                tickvals: data.days,
                range: [Math.min(...data.days) - 0.3, Math.max(...data.days) + 0.3],
                showline: true,
                mirror: false,
            };
            const yaxis = {
                anchor: axisNumber === 1 ? "x" : `x${axisNumber}`,
                showline: true,
                showgrid: true,
                gridcolor: "rgba(0,0,0,0.12)",
                zeroline: false,
            };

            if (axisNumber > 1) {
                xaxis.matches = "x";
                yaxis.matches = "y";
                yaxis.showticklabels = false;
            } else {
                yaxis.title = { text: "Hemolysis %" };
            }

            layout[xaxisKey] = xaxis;
            layout[yaxisKey] = yaxis;
            layout.annotations.push({
                text: `Group ${group.name} (n = ${group.subject_count})`,
                x: (start + end) / 2,
                y: 1.12,
                xref: "paper",
                yref: "paper",
                showarrow: false,
                font: { color: group.color, size: 14 },
            });
        });
        layout.annotations.push({
            text: `One-way ANOVA between groups (alpha = ${data.alpha}):`,
            x: 0.02,
            y: -0.08,
            xref: "paper",
            yref: "paper",
            xanchor: "left",
            showarrow: false,
            font: { size: 12 },
        });
        data.decisions.forEach((decision, index) => {
            layout.annotations.push({
                text: decision.text,
                x: 0.04,
                y: -0.16 - index * 0.07,
                xref: "paper",
                yref: "paper",
                xanchor: "left",
                showarrow: false,
                font: { color: decision.significant ? "#b2182b" : "#444", size: 11 },
            });
        });
        return layout;
    }

    async function renderChart(data) {
        const traces = createTraces(data);
        await Plotly.react(plotElement, traces, createLayout(data), {
            responsive: true,
            displaylogo: false,
        });
        const traceElements = plotElement.querySelectorAll(".scatterlayer .trace");
        traces.forEach((trace, traceIndex) => {
            if (trace.meta?.type !== "measurement" || !traceElements[traceIndex]) {
                return;
            }
            traceElements[traceIndex].querySelectorAll(".points .point").forEach((point, pointIndex) => {
                point.dataset.pointId = trace.meta.point_ids[pointIndex];
            });
        });
    }

    function setStatus(message, isError = false) {
        statusElement.textContent = message;
        statusElement.classList.toggle("error", isError);
    }

    function updateTables(response) {
        document.getElementById("group-statistics-table").innerHTML = response.group_table;
        document.getElementById("anova-results-table").innerHTML = response.anova_table;
    }

    async function recalculate() {
        const currentRequest = ++requestNumber;
        const requestedExcludedIds = [...excludedPointIds];
        setStatus("Updating statistics…");
        await renderChart(plotData);

        try {
            const response = await fetch("/recalculate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    upload_id: uploadId,
                    excluded_point_ids: requestedExcludedIds,
                    alpha: Number(alphaInput.value),
                }),
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || "Could not recalculate the statistics.");
            }
            if (currentRequest !== requestNumber) {
                return;
            }

            plotData = result.plot_data;
            excludedPointIds = new Set(plotData.excluded_point_ids);
            committedExcludedPointIds = new Set(excludedPointIds);
            updateTables(result);
            await renderChart(plotData);
            setStatus(`${excludedPointIds.size} measurement(s) excluded.`);
        } catch (error) {
            if (currentRequest !== requestNumber) {
                return;
            }
            excludedPointIds = new Set(committedExcludedPointIds);
            await renderChart(plotData);
            setStatus(error.message, true);
        }
    }

    plotElement.addEventListener("contextmenu", (event) => {
        event.preventDefault();
        const hoveredPoint = (plotElement._hoverdata || []).find(
            (point) => point.data?.meta?.type === "measurement" && point.customdata
        );
        const clickedPoint = event.target.closest?.("[data-point-id]");
        let pointId = clickedPoint?.dataset.pointId;
        if (!pointId) {
            let nearestDistance = 12;
            plotElement.querySelectorAll(".point[data-point-id]").forEach((point) => {
                const bounds = point.getBoundingClientRect();
                const dx = event.clientX - (bounds.left + bounds.width / 2);
                const dy = event.clientY - (bounds.top + bounds.height / 2);
                const distance = Math.hypot(dx, dy);
                if (distance < nearestDistance) {
                    nearestDistance = distance;
                    pointId = point.dataset.pointId;
                }
            });
        }
        pointId ||= hoveredPoint?.customdata?.[0];
        if (!pointId) {
            return;
        }

        if (excludedPointIds.has(pointId)) {
            excludedPointIds.delete(pointId);
        } else {
            excludedPointIds.add(pointId);
        }
        recalculate();
    });

    renderChart(plotData);
})();
