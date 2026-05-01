<script lang="ts">
    import OccurrencesGraphic from '../OccurrencesGraphic.svelte';
    import './aboutModals.css';
</script>

<div id="occurrences-modal" class="about-modal-wrapper">
    <h3 class="modal-header">Occurrences</h3>
    <p class="modal-subheader">
        The estimate of the number of distinct populations of a given species
    </p>
    <div class="modal-body">
        <div class="occurrences-text-and-diagram">
            <div class="occurrences-top-text">
                <p>
                    A simple way of imagining an occurrence of a species is to
                    picture two ants of the same species. When found within the
                    same anthill, these two ants would not likely represent
                    distinct occurrences. On the other hand, if these two ants
                    were found on opposite sides of Texas, they would likely
                    represent two distinct occurrences of the same species.
                </p>
            </div>
            <div class="occurrences-graphic">
                <OccurrencesGraphic />
            </div>
        </div>
        <div class="occurrences-text">
            <div>
                <p>
                    While this metric should ideally be derived through an
                    in-depth and highly personalized process for each species,
                    for the purposes of this tool, it is approximated as the
                    number of distinct clusters of observations given a
                    separation distance (default: 1km).
                </p>
                <p>
                    On our server, this calculation is performed using an
                    EPSG:5070 projection when calculating separation distance.
                    While no projection is perfect, EPSG:5070 is accurate within
                    a few meters while comparing points with a 1km separation
                    distance within Texas and allows for timely calculations and
                    results while filtering data points.
                </p>
            </div>
        </div>
    </div>
</div>

<style>
    .occurrences-top-text {
        flex: 1 1 500px;
        max-width: 100%;
        min-width: 0;
    }
    .occurrences-text-and-diagram {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .occurrences-graphic {
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        flex-grow: 1;
    }
</style>
