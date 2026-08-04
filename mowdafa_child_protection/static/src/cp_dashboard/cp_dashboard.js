/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

/**
 * Child Protection dashboard — one screen, two halves.
 *
 * One RPC (cp.case.get_dashboard_data) returns both: the managed
 * caseload (cp.case: stages, recommendations) and the partner report
 * (cp.partner.record: by agency, region, concern, sex, age, status).
 * They share a screen but never a number — "cases we handle" and
 * "records we hold" stay clearly apart.
 */
const RECO_COLORS = {
    reunification: "#0ca30c",
    reunification_support: "#2a78d6",
    alt_care: "#eda100",
    tracing: "#d03b3b",
};

export class CpDashboard extends Component {
    static template = "mowdafa_child_protection.CpDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.user = useService("user");
        this.state = useState({
            loading: true, data: null, caseType: null,
            canStreet: false, canCaafag: false, canAll: false,
        });
        onWillStart(async () => {
            const [street, caafag] = await Promise.all([
                this.user.hasGroup("mowdafa_child_protection.group_cp_street"),
                this.user.hasGroup("mowdafa_child_protection.group_cp_caafag"),
            ]);
            this.state.canStreet = street;
            this.state.canCaafag = caafag;
            // "All" only makes sense when a user may see both types
            this.state.canAll = street && caafag;
            // a single-type user is locked to their type from the start
            if (!this.state.canAll) {
                this.state.caseType = street ? "street"
                    : caafag ? "caafag" : null;
            }
            await this.load();
        });
    }

    async load() {
        this.state.loading = true;
        this.state.data = await this.orm.call(
            "cp.case", "get_dashboard_data", [this.state.caseType]);
        this.state.loading = false;
    }

    async setCaseType(caseType) {
        this.state.caseType = caseType;
        await this.load();
    }

    // domain fragment that carries the active filter into drill-throughs
    get caseDomain() {
        return this.state.caseType
            ? [["case_type", "=", this.state.caseType]]
            : [];
    }

    get tiles() {
        return this.state.data.tiles;
    }

    recoColor(key) {
        return RECO_COLORS[key] || "#4a3aa7";
    }

    pct(value, total) {
        return total ? ((value / total) * 100).toFixed(0) + "%" : "0%";
    }

    _bars(rows) {
        const max = Math.max(...rows.map((r) => r.count), 1);
        return rows.map((r) => ({
            ...r,
            widthPct: ((r.count / max) * 100).toFixed(1),
        }));
    }

    // ── managed track ────────────────────────────────────────────────
    get stageBars() {
        return this._bars(this.state.data.stages);
    }

    get recoBars() {
        return this._bars(this.state.data.recommendations).map((r) => ({
            ...r,
            color: this.recoColor(r.key),
        }));
    }

    // ── partner report ───────────────────────────────────────────────
    get regionBars() {
        return this._bars(this.state.data.partner_regions);
    }

    get concernBars() {
        return this._bars(this.state.data.partner_concerns);
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

    get agencyRows() {
        const rows = this.state.data.partner_agencies;
        const total = rows.reduce((s, r) => s + r.children, 0) || 1;
        return rows.map((r) => ({
            ...r,
            sharePct: ((r.children / total) * 100).toFixed(0) + "%",
            barPct: ((r.children / total) * 100).toFixed(1),
        }));
    }

    get agencyTotals() {
        const rows = this.state.data.partner_agencies;
        return {
            children: rows.reduce((s, r) => s + r.children, 0),
            active: rows.reduce((s, r) => s + r.active, 0),
            closed: rows.reduce((s, r) => s + r.closed, 0),
            critical: rows.reduce((s, r) => s + r.critical, 0),
        };
    }

    // status colour never travels alone — it always ships with an icon
    statusTone(name) {
        return {
            "Active": "is-good",
            "Pending": "is-warning",
            "Closed": "is-neutral",
            "Critical/High": "is-critical",
        }[name] || "";
    }

    statusIcon(name) {
        return {
            "Active": "fa-check-circle",
            "Pending": "fa-clock-o",
            "Closed": "fa-archive",
            "Critical/High": "fa-exclamation-triangle",
        }[name] || "fa-circle";
    }

    // ── drill-through ────────────────────────────────────────────────
    openCases(resModel, domain, title) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: title,
            res_model: resModel,
            views: [[false, "list"], [false, "form"]],
            domain: domain || [],
            target: "current",
        });
    }

    openManaged() {
        this.openCases("cp.case", this.caseDomain, "Cases");
    }

    openPartner() {
        this.openCases("cp.partner.record", [], "Partner Children");
    }

    openPartnerActive() {
        this.openCases("cp.partner.record",
            [["case_status", "in", ["open", "active"]]], "Active");
    }

    openPartnerClosed() {
        this.openCases("cp.partner.record",
            [["case_status", "=", "closed"]], "Closed");
    }

    openPartnerCritical() {
        this.openCases("cp.partner.record",
            [["risk_level", "in", ["critical", "high"]]], "Critical Risk");
    }
}

registry.category("actions").add(
    "mowdafa_child_protection.cp_dashboard", CpDashboard);
