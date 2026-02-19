import type { Component } from 'svelte';
import { type ModalState } from '../contexts/modalContext';

// Function to handle opening the modal component
export function openModal(
    modalContext: ModalState,
    content: string | Component
) {
    modalContext.content = content;
    modalContext.visible = true;
}
