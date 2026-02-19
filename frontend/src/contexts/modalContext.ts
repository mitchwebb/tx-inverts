import { getContext, setContext, type Component, type Snippet } from 'svelte';

export const ModalStateKey = 'modal';

export type ModalState = {
    visible: boolean;
    content: string | Component | null;
};

export const initialModalState: ModalState = {
    visible: false,
    content: null,
};

export function setModalContext(ModalState: ModalState) {
    setContext(ModalStateKey, ModalState);
}

export function getModalContext(): ModalState {
    return getContext(ModalStateKey) as ModalState;
}
