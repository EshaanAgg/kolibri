<template>

  <KIconButton
    hasDropdown
    icon="optionsHorizontal"
    appearance="flat-button"
    :ariaLabel="coreString('optionsLabel')"
  >
    <template #menu>
      <KDropdownMenu
        :options="options"
        @select="$emit('select', $event.value)"
      />
    </template>
  </KIconButton>

</template>


<script>

  import commonCoreStrings from 'kolibri.coreVue.mixins.commonCoreStrings';
  import { coachStringsMixin } from '../../common/commonCoachStrings';

  export default {
    name: 'LessonOptionsDropdownMenu',
    mixins: [coachStringsMixin, commonCoreStrings],
    props: {
      // Should be 'report' or 'plan'
      optionsFor: {
        type: String,
        required: true,
      },
    },
    computed: {
      options() {
        const editDetails = {
          label: this.coreString('editDetailsAction'),
          value: 'EDIT_DETAILS',
        };

        if (this.optionsFor === 'plan') {
          return [
            editDetails,
            {
              label: this.$tr('copyLessonAction'),
              value: 'COPY',
            },
            {
              label: this.coachString('printReportAction'),
              value: 'PRINT_REPORT',
            },
            {
              label: this.coachString('exportCSVAction'),
              value: 'EXPORT',
            },
            { label: this.coreString('deleteAction'), value: 'DELETE' },
          ];
        }

        return [
          editDetails,
          {
            label: this.coachString('manageResourcesAction'),
            value: 'MANAGE_RESOURCES',
          },
          {
            label: this.coachString('printReportAction'),
            value: 'PRINT_REPORT',
          },
          {
            label: this.coachString('exportCSVAction'),
            value: 'EXPORT',
          },
        ];
      },
    },
    $trs: {
      copyLessonAction: {
        message: 'Copy lesson',
        context:
          "Coaches can copy lessons to a different group or another class of their facility.\n\nThe 'Copy lesson' option appears in the Plan > Lessons section.",
      },
    },
  };

</script>


<style lang="scss" scoped></style>
