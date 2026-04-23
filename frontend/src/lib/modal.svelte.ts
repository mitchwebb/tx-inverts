import type { Component, Snippet } from 'svelte';
import { type ModalState } from '../contexts/modalContext';

// Function to handle opening the modal component
export function openModal(modalContext: ModalState, content: string | Snippet) {
    modalContext.content = content;
    modalContext.visible = true;
}
