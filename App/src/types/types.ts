export interface VTreeNode {
    code?: string;
    children?: VTreeNode[];
    name?: string;
    label?: string;
    "label-en"?: string;
    position?: number;
    level?: number;
    pattern?: number;
    is_intermediate_code?: boolean;
    full_typecode?: string;
    group?: string;
}

export interface VTree extends VTreeNode {
    children?: VTreeNode[];
}

export interface ProductFamily extends VTreeNode {
    code: string;
    position: 1;
    level: 1;
}

export interface Selection {
    familyCode: string;
    groups: Record<number, VTreeNode>;
    levels?: Record<number, VTreeNode>;
}

export interface AvailableOption {
    node: VTreeNode;
    isSelectable: boolean;
    isIntermediate: boolean;
    isCompatible: boolean;
}

export interface GroupInfo {
    position: number;
    level?: number;
    pattern: number;
    name: string;
    availableOptions: AvailableOption[];
    selectedOption?: VTreeNode;
}
