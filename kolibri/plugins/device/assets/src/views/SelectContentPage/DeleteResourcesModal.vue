<template>

  <KModal
    :title="title"
    :submitText="coreString('deleteAction')"
    :cancelText="coreString('cancelAction')"
    @submit="$emit('submit', { deleteEverywhere })"
    @cancel="$emit('cancel')"
  >
    <div>
      <template v-if="numberOfResources === 1">
        <p>{{ $tr('confirmationQuestionOneResource') }}</p>
        <p>{{ $tr('deleteEverywhereExplanationOneResource') }}</p>
      </template>
      <template v-else>
        <p>{{ $tr('confirmationQuestionMultipleResources') }}</p>
        <p>{{ $tr('deleteEverywhereExplanationMultipleResources') }}</p>
      </template>
      <KCheckbox
        :checked="deleteEverywhere"
        :label="$tr('deleteEverywhereLabel')"
        @change="deleteEverywhere = !deleteEverywhere"
      />
      <p>{{ coreString('cannotUndoActionWarning') }}</p>
    </div>
  </KModal>

</template>


<script>

  import commonCoreStrings from 'kolibri.coreVue.mixins.commonCoreStrings';

  export default {
    name: 'DeleteResourcesModal',
    mixins: [commonCoreStrings],
    props: {
      numberOfResources: {
        type: Number,
        required: true,
      },
    },
    data() {
      return {
        deleteEverywhere: false,
      };
    },
    computed: {
      title() {
        return this.numberOfResources === 1
          ? this.$tr('titleSingleResource')
          : this.$tr('titleMultipleResources');
      },
    },
    $trs: {
      titleMultipleResources: {
        message: 'Delete resources',
        context:
          'Title of window that displays when user deletes multiple learning resources from a channel.',
      },
      titleSingleResource: {
        message: 'Delete resource',
        context:
          'Title of window that displays when user deletes a single learning resource from a channel.',
      },
      confirmationQuestionOneResource: {
        message: 'Are you sure you want to delete this resource from your device?',
        context: 'Confirmation of single resource deletion.',
      },
      confirmationQuestionMultipleResources: {
        message: 'Are you sure you want to delete these resources from your device?',
        context: 'Confirmation of multiple resource deletion.',
      },
      deleteEverywhereLabel: {
        message: 'Also delete any copies found in other locations and channels',
        context:
          'When some of the resources the admin selected are present in multiple channels, Kolibri will provide an option for the admin to delete all instances ',
      },
      deleteEverywhereExplanationOneResource: {
        message: 'Some copies of this resource may be in other locations on your device',
        context:
          'When some of the resources admin selected are present in multiple channels, Kolibri will provide an option for the admin to delete all instances ',
      },
      deleteEverywhereExplanationMultipleResources: {
        message: 'Some copies of these resources may be in other locations on your device',
        context:
          'When some of the resources the admin selected are present in multiple channels, Kolibri will provide an option for the admin to delete all instances ',
      },
    },
  };

</script>


<style lang="scss" scoped></style>
