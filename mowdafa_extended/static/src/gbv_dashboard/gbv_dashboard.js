/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

/**
 * GBV Dashboard.
 *
 * One RPC (gbv.case.get_dashboard_data) returns every aggregate; the
 * charts below are hand-rolled SVG/CSS so the dashboard has no external
 * chart dependency and mirrors the approved design: KPI tiles, cases by
 * region, status and gender donuts, age bands, violence types, service
 * referrals, monthly trend and the access-to-justice funnel.
 */
export class GbvDashboard extends Component {
    static template = "mowdafa_extended.GbvDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            year: false,
            regionId: false,
            data: null,
        });
        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = true;
        this.state.data = await this.orm.call(
            "gbv.case", "get_dashboard_data", [],
            { year: this.state.year, region_id: this.state.regionId },
        );
        this.state.year = this.state.data.year;
        this.state.regionId = this.state.data.region_id;
        this.state.loading = false;
    }

    onYearChange(ev) {
        this.state.year = parseInt(ev.target.value, 10);
        this.load();
    }

    onRegionChange(ev) {
        this.state.regionId = ev.target.value
            ? parseInt(ev.target.value, 10) : false;
        this.load();
    }

    // ------------------------------------------------------------------
    // Formatting helpers
    // ------------------------------------------------------------------
    fmt(value) {
        return new Intl.NumberFormat("en-US").format(value || 0);
    }

    pct(value, total) {
        return total ? ((value / total) * 100).toFixed(1) + "%" : "0%";
    }

    get totals() {
        return this.state.data.totals;
    }

    /** Year-on-year growth of total cases, e.g. "+19.0%". */
    get deltaText() {
        const { total, prev_total } = this.totals;
        if (!prev_total) {
            return "";
        }
        const delta = ((total - prev_total) / prev_total) * 100;
        return (delta >= 0 ? "▲ +" : "▼ ") + delta.toFixed(1) +
            "% vs " + this.fmt(prev_total);
    }

    // ------------------------------------------------------------------
    // Drill-down: every tile opens the underlying case list
    // ------------------------------------------------------------------
    openCases(title, extraDomain) {
        const data = this.state.data;
        const domain = [
            ["date_reported", ">=", `${data.year}-01-01`],
            ["date_reported", "<=", `${data.year}-12-31`],
            ...(extraDomain || []),
        ];
        if (data.region_id) {
            domain.push(["region_id", "=", data.region_id]);
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: `${title} — ${data.year}`,
            res_model: "gbv.case",
            views: [[false, "list"], [false, "form"]],
            domain,
            target: "current",
        });
    }

    // ------------------------------------------------------------------
    // Donuts (status, gender) — SVG stroke-dasharray segments
    // ------------------------------------------------------------------
    _donut(items) {
        const RADIUS = 52;
        const CIRC = 2 * Math.PI * RADIUS;
        const total = items.reduce((sum, item) => sum + item.value, 0);
        let offset = 0;
        return items.map((item) => {
            const length = total ? (CIRC * item.value) / total : 0;
            const segment = {
                ...item,
                radius: RADIUS,
                dash: `${length.toFixed(2)} ${(CIRC - length).toFixed(2)}`,
                offset: (-offset).toFixed(2),
            };
            offset += length;
            return segment;
        });
    }

    get statusDonut() {
        const t = this.totals;
        return this._donut([
            { label: "Open", value: t.open, color: "#2E75B6" },
            { label: "Closed", value: t.closed, color: "#1F4E79" },
            { label: "In Court", value: t.court, color: "#C77D18" },
        ]);
    }

    get genderDonut() {
        const t = this.totals;
        return this._donut([
            { label: "Female", value: t.female, color: "#157F76" },
            { label: "Male", value: t.male, color: "#A6AEB2" },
        ]);
    }

    // ------------------------------------------------------------------
    // Cases by region — CSS stacked bars with year-on-year delta
    // ------------------------------------------------------------------
    get regionRows() {
        const rows = this.state.data.regions;
        const max = Math.max(...rows.map((row) => row.total), 1);
        return rows.map((row) => {
            let deltaText = "";
            let deltaUp = true;
            if (row.prev) {
                const delta = ((row.total - row.prev) / row.prev) * 100;
                deltaUp = delta >= 0;
                deltaText = (deltaUp ? "▲" : "▼") +
                    Math.abs(delta).toFixed(1) + "%";
            }
            return {
                ...row,
                widthPct: ((row.total / max) * 100).toFixed(1),
                deltaText,
                deltaUp,
            };
        });
    }

    // ------------------------------------------------------------------
    // Age bands — SVG vertical bars, children highlighted
    // ------------------------------------------------------------------
    get ageChart() {
        const WIDTH = 420;
        const HEIGHT = 160;
        const bands = this.state.data.ages;
        const barWidth = 30;
        const gap = (WIDTH - bands.length * barWidth) / (bands.length + 1);
        const max = Math.max(...bands.map((band) => band.count), 1);
        const bars = bands.map((band, index) => {
            const height = (band.count / max) * (HEIGHT - 52);
            const x = gap + index * (barWidth + gap);
            return {
                ...band,
                x: x.toFixed(1),
                y: (HEIGHT - 20 - height).toFixed(1),
                width: barWidth,
                height: Math.max(height, 0).toFixed(1),
                labelX: (x + barWidth / 2).toFixed(1),
                valueY: (HEIGHT - 24 - height).toFixed(1),
                color: band.is_child ? "#C77D18" : "#2E75B6",
            };
        });
        // Divider between the last child band (16-17) and the adult bands.
        const childCount = bands.filter((band) => band.is_child)
            .reduce((sum, band) => sum + band.count, 0);
        const total = this.totals.total;
        return {
            width: WIDTH,
            height: HEIGHT,
            bars,
            dividerX: (gap + 5 * (barWidth + gap) - gap / 2).toFixed(1),
            childText: `children ${this.fmt(childCount)} · ` +
                this.pct(childCount, total),
            adultText: `adults ${this.fmt(total - childCount)} · ` +
                this.pct(total - childCount, total),
        };
    }

    // ------------------------------------------------------------------
    // Violence types & service referrals — CSS horizontal bars
    // ------------------------------------------------------------------
    _hbars(rows, denominator) {
        const max = Math.max(...rows.map((row) => row.count), 1);
        return rows.map((row) => ({
            ...row,
            widthPct: ((row.count / max) * 100).toFixed(1),
            pctText: this.pct(row.count, denominator),
        }));
    }

    get typeRows() {
        return this._hbars(this.state.data.types, this.totals.total);
    }

    get serviceRows() {
        return this._hbars(this.state.data.services, this.totals.total);
    }

    // ------------------------------------------------------------------
    // Monthly trend — SVG line + area
    // ------------------------------------------------------------------
    get monthChart() {
        const WIDTH = 420;
        const HEIGHT = 140;
        const months = this.state.data.months;
        const max = Math.max(...months.map((month) => month.count), 1);
        const step = (WIDTH - 44) / (months.length - 1);
        const dots = months.map((month, index) => ({
            ...month,
            x: (26 + index * step).toFixed(1),
            y: (HEIGHT - 24 - (month.count / max) * (HEIGHT - 44)).toFixed(1),
        }));
        const line = dots.map((dot) => `${dot.x},${dot.y}`).join(" ");
        const area = `26,${HEIGHT - 24} ${line} ` +
            `${dots[dots.length - 1].x},${HEIGHT - 24}`;
        return { width: WIDTH, height: HEIGHT, dots, line, area, max };
    }

    // ------------------------------------------------------------------
    // Access to justice — centred funnel with drop-off per stage
    // ------------------------------------------------------------------
    get funnelRows() {
        const stages = this.state.data.funnel;
        const top = stages.length ? Math.max(stages[0].count, 1) : 1;
        return stages.map((stage, index) => {
            let dropText = this.pct(stage.count, this.totals.total);
            let isDrop = false;
            if (index > 0 && stages[index - 1].count) {
                const drop = 100 - (stage.count / stages[index - 1].count) * 100;
                dropText = "−" + drop.toFixed(0) + "%";
                isDrop = true;
            }
            return {
                ...stage,
                widthPct: Math.max((stage.count / top) * 100, 2).toFixed(1),
                opacity: (1 - index * 0.13).toFixed(2),
                dropText,
                isDrop,
            };
        });
    }

    get convictionText() {
        const t = this.totals;
        return this.pct(t.convicted, t.total) +
            " of reported cases end in a conviction.";
    }
}

registry.category("actions").add(
    "mowdafa_extended.gbv_dashboard", GbvDashboard);
