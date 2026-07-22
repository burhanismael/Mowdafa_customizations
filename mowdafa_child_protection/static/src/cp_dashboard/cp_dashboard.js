/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

/**
 * Child Protection dashboard.
 *
 * One RPC (cp.case.get_dashboard_data). Two halves, matching the two
 * tracks: the managed caseload (stages, recommendations) and the
 * partner report (by agency, region, concern, sex) — kept apart so
 * "cases we handle" never blurs into "records we hold".
 */
const RECO_COLORS = {
    reunification: "#1E7A44",
    reunification_support: "#2E75B6",
    alt_care: "#8C560D",
    tracing: "#C0392B",
};

export class CpDashboard extends Component {
    static template = "mowdafa_child_protection.CpDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ loading: true, data: null });
        onWillStart(async () => {
            this.state.data = await this.orm.call(
                "cp.case", "get_dashboard_data", []);
            this.state.loading = false;
        });
    }

    get tiles() {
        return this.state.data.tiles;
    }

    recoColor(key) {
        return RECO_COLORS[key] || "#5B3A78";
    }

    _bars(rows) {
        const max = Math.max(...rows.map((r) => r.count), 1);
        return rows.map((r) => ({
            ...r,
            widthPct: ((r.count / max) * 100).toFixed(1),
        }));
    }

    get stageBars() {
        return this._bars(this.state.data.stages);
    }

    get recoBars() {
        return this._bars(this.state.data.recommendations).map((r) => ({
            ...r,
            color: this.recoColor(r.key),
        }));
    }

    get regionBars() {
        return this._bars(this.state.data.partner_regions);
    }

    get concernBars() {
        return this._bars(this.state.data.partner_concerns);
    }

    get agencyRows() {
        const rows = this.state.data.partner_agencies;
        const total = rows.reduce((s, r) => s + r.children, 0) || 1;
        return rows.map((r) => ({
            ...r,
            sharePct: ((r.children / total) * 100).toFixed(0) + "%",
        }));
    }

    get sexBars() {
        return this._bars(this.state.data.partner_sex);
    }

    get ageBars() {
        return this._bars(this.state.data.partner_ages);
    }

    get statusBars() {
        return this._bars(this.state.data.partner_status);
    }

    pct(value, total) {
        return total ? ((value / total) * 100).toFixed(0) + "%" : "0%";
    }

    openCases(domain, title) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: title,
            res_model: "cp.case",
            views: [[false, "list"], [false, "form"]],
            domain,
            target: "current",
        });
    }

    openManaged() {
        this.openCases([["record_type", "=", "managed"]], "Cases");
    }

    openPartner() {
        this.openCases([["record_type", "=", "partner"]], "Partner Children");
    }
}

registry.category("actions").add(
    "mowdafa_child_protection.cp_dashboard", CpDashboard);
