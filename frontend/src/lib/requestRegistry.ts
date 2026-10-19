// Owns all request controllers for abort reasons
// Realistically, this is only needed for taxon requests
type RequestKey = string;

export const controllers = new Map<RequestKey, AbortController>();

// Create controller key using taxonID and request type
function key(taxonID: string, kind: string): RequestKey {
    return `${taxonID}:${kind}`;
}

/**
 * Function for adding requests to internal register of AbortControllers
 *
 * @param taxonID
 * @param kind // Identifier for the source of the request EG: "tiles", "nSMetrics"
 * @returns
 */
export function registerRequest(
    taxonID: string,
    kind: string
): AbortController {
    const controllerKey = key(taxonID, kind);
    controllers.get(controllerKey)?.abort();
    const controller = new AbortController();
    controllers.set(controllerKey, controller);
    return controller;
}

/**
 * Function for giving request callers the ability to delete their own controller on completion.
 *
 * @param taxonID
 * @param kind
 * @param controller
 */
export function resolveRequest(
    taxonID: string,
    kind: string,
    controller: AbortController
) {
    const controllerKey = key(taxonID, kind);
    if (controllers.get(controllerKey) === controller) {
        controllers.delete(controllerKey);
    }
}

export function abortRequest(taxonID: string, kind: string): void {
    const controllerKey = key(taxonID, kind);
    controllers.get(controllerKey)?.abort();
    controllers.delete(controllerKey);
}

/**
 * Matching key format for requestRegistry module, uses taxonID to
 * cancel and delete all matching requests from the requestRegistry
 *
 * @param taxonID
 */
export function abortAllIDRequests(taxonID: string) {
    for (const controller of controllers.keys()) {
        if (controller.startsWith(`${taxonID}:`)) {
            controllers.get(controller)?.abort();
            controllers.delete(controller);
        }
    }
}
