/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const STAGE_ICONS = {
    reported: "fa-circle-o text-muted",
    investigated: "fa-exclamation-circle text-warning",
    arrested: "fa-dot-circle-o text-danger",
    in_court: "fa-gavel text-primary",
    convicted: "fa-check-circle text-success",
};

export class JusticeStageField extends Component {
    static template = "mowdafa_extended.JusticeStageField";
    static components = { Dropdown, DropdownItem };
    static props = { ...standardFieldProps };

    get options() {
        return this.props.record.fields[this.props.name].selection.filter(
            ([value]) => value !== false
        );
    }

    get currentValue() {
        return this.props.record.data[this.props.name];
    }

    get currentLabel() {
        const option = this.options.find(([value]) => value === this.currentValue);
        return option ? option[1] : "";
    }

    icon(value) {
        return STAGE_ICONS[value] || "fa-circle-o text-muted";
    }

    async selectStage(value) {
        await this.props.record.update({ [this.props.name]: value });
    }
}

export const justiceStageField = {
    component: JusticeStageField,
    supportedTypes: ["selection"],
};

registry.category("fields").add("justice_stage_selection", justiceStageField);
