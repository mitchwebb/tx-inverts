import { expect, test } from 'vitest';
import { getHumanReadableBytes } from './bytes';

test('getHumanReadableBytes returns appropriate units', () => {
    expect(getHumanReadableBytes(1)).toContain('Bytes');
    expect(getHumanReadableBytes(Math.pow(1024, 1))).toContain('KB');
    expect(getHumanReadableBytes(Math.pow(1024, 2))).toContain('MB');
    expect(getHumanReadableBytes(Math.pow(1024, 3))).toContain('GB');
    expect(getHumanReadableBytes(Math.pow(1024, 4))).toContain('TB');
    expect(getHumanReadableBytes(Math.pow(1024, 5))).toContain('PB');
    expect(getHumanReadableBytes(Math.pow(1024, 6))).toContain('EB');
    expect(getHumanReadableBytes(Math.pow(1024, 7))).toContain('ZB');
    expect(getHumanReadableBytes(Math.pow(1024, 8))).toContain('YB');
});

test('getHumanReadableBytes returns correct value', () => {
    expect(getHumanReadableBytes(Math.pow(512, 2))).toContain('256 KB');
    expect(getHumanReadableBytes(Math.pow(512, 4))).toContain('64 GB');
    expect(getHumanReadableBytes(Math.pow(1000, 2))).toContain('.95 MB');
});

// Units will fail if too high of a number (larger than yottabytes)
test('getHumanReadableBytes returns failed value as string', () => {
    expect(getHumanReadableBytes(10000000000000000000000000000)).toContain(
        '1e+28 Bytes'
    );
});
