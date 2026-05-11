import type { RouterPath } from './router';

export type NavItem = {
    label: string;
    href: RouterPath;
    children?: NavItem[];
};
