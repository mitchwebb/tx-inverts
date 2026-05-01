<script lang="ts">
    import RangeExtentAnimation from '../RangeExtentAnimation.svelte';
    import './aboutModals.css';
</script>

<div class="about-modal-wrapper">
    <h3 class="modal-header">Range Extent</h3>
    <div class="modal-subheader">
        The smallest continuous area containing all observations of a species
        (km<sup>2</sup>)
    </div>
    <div class="modal-body">
        <div class="range-text-and-diagram">
            <div class="range-text">
                <p>
                    Our range extent metric is calculated by drawing a polygon
                    around all known observations of a species and measuring its
                    area. Although there are different methods for creating this
                    polygon (with convex hulls and α-hulls being cited in
                    NatureServe documentation), we've chosen to use the minimum
                    convex hull method. Although this method tends to
                    overestimate the populated area, it is an efficient method
                    that is used in NatureServe's RARECAT tool.
                </p>
            </div>

            <div class="range-extent-animation">
                <RangeExtentAnimation />
            </div>
        </div>
    </div>
</div>

<style>
    .range-text {
        flex: 1 1 500px;
        max-width: 100%;
        min-width: 0;
    }
    .range-text-and-diagram {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .range-extent-animation {
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        flex-grow: 1;
    }
</style>
