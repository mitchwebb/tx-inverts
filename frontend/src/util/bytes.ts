/**
 * Takes size in bytes and returns human-readable string with units (up to YB)
 *
 * Falls back to input value with 'Bytes' if failed to parse
 *
 * @param bytes - Size in bytes
 * @returns A human readable string with size units
 */
export function getHumanReadableBytes(bytes: number): string {
    let sizes = [
        ' Bytes',
        ' KB',
        ' MB',
        ' GB',
        ' TB',
        ' PB',
        ' EB',
        ' ZB',
        ' YB',
    ];

    for (let i = 1; i <= sizes.length; i++) {
        if (bytes < Math.pow(1000, i))
            return (
                parseFloat((bytes / Math.pow(1024, i - 1)).toFixed(2)) +
                sizes[i - 1]
            );
    }
    return bytes.toString() + ' Bytes';
}
