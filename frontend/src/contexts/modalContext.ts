import { getContext, setContext, type Component, type Snippet } from 'svelte';

export const ModalStateKey = 'modal';

export type ModalStateType = {
    visible: boolean;
    content: string | Component | null;
};

export const initialModalState: ModalStateType = {
    visible: false,
    content: null,
};

export function setModalContext(ModalState: ModalStateType) {
    setContext(ModalStateKey, ModalState);
}

export function getModalContext(): ModalStateType {
    return getContext(ModalStateKey) as ModalStateType;
}
