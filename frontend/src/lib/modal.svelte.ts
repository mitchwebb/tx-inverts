import type { Component } from 'svelte';
import { type ModalStateType } from '../contexts/modalContext';

// Function to handle opening the modal component
export function openModal(
    modalContext: ModalStateType,
    content: string | Component
) {
    modalContext.content = content;
    modalContext.visible = true;
}
